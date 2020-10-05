import time

from dagster import check
from dagster.core.errors import DagsterIncompleteExecutionPlanError, DagsterUnknownStepStateError
from dagster.core.events import DagsterEvent
from dagster.core.execution.retries import Retries
from dagster.utils import pop_delayed_interrupts

from .plan import ExecutionPlan


def _default_sort_key(step):
    return int(step.tags.get("dagster/priority", 0)) * -1


class ActiveExecution(object):
    """State machine used to track progress through execution of an ExecutionPlan
    """

    def __init__(self, execution_plan, retries, sort_key_fn=None):
        self._plan = check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        self._retries = check.inst_param(retries, "retries", Retries)
        self._sort_key_fn = check.opt_callable_param(sort_key_fn, "sort_key_fn", _default_sort_key)

        self._context_guard = False  # Prevent accidental direct use

        # All steps to be executed start out here in _pending
        self._pending = self._plan.execution_deps()

        # steps move in to these buckets as a result of _update calls
        self._executable = []
        self._pending_skip = []
        self._pending_retry = []
        self._pending_abandon = []
        self._waiting_to_retry = {}

        # then are considered _in_flight when vended via get_steps_to_*
        self._in_flight = set()

        # and finally their terminal state is tracked by these sets, via mark_*
        self._success = set()
        self._failed = set()
        self._skipped = set()
        self._abandoned = set()

        # see verify_complete
        self._unknown_state = set()
        self._interrupted = set()

        # Start the show by loading _executable with the set of _pending steps that have no deps
        self._update()

    def __enter__(self):
        self._context_guard = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._context_guard = False

        # Exiting due to exception, return to allow exception to bubble
        if exc_type or exc_value or traceback:
            return

        # Requested termination is the only time we should be exiting incomplete without an exception
        if not self.is_complete:
            pending_action = (
                self._executable + self._pending_abandon + self._pending_retry + self._pending_skip
            )
            raise DagsterIncompleteExecutionPlanError(
                "Execution of pipeline finished without completing the execution plan, "
                "likely as a result of a termination request."
                "{pending_str}{in_flight_str}{action_str}{retry_str}".format(
                    in_flight_str="\nSteps still in flight: {}".format(self._in_flight)
                    if self._in_flight
                    else "",
                    pending_str="\nSteps pending processing: {}".format(self._pending.keys())
                    if self._pending
                    else "",
                    action_str="\nSteps pending action: {}".format(pending_action)
                    if pending_action
                    else "",
                    retry_str="\nSteps waiting to retry: {}".format(self._waiting_to_retry.keys())
                    if self._waiting_to_retry
                    else "",
                )
            )

        # See verify_complete - steps for which we did not observe a failure/success event are in an unknown
        # state so we raise to ensure pipeline failure.
        if len(self._unknown_state) > 0:
            raise DagsterUnknownStepStateError(
                "Execution of pipeline exited with steps {step_list} in an unknown state to this process.\n"
                "This was likely caused by losing communication with the process performing step execution.".format(
                    step_list=self._unknown_state
                )
            )

    def _update(self):
        """Moves steps from _pending to _executable / _pending_skip / _pending_retry
           as a function of what has been _completed
        """
        new_steps_to_execute = []
        new_steps_to_skip = []
        new_steps_to_abandon = []

        successful_or_skipped_steps = self._success | self._skipped
        failed_or_abandoned_steps = self._failed | self._abandoned

        for step_key, requirements in self._pending.items():
            # If any upstream deps failed - this is not executable
            if requirements.intersection(failed_or_abandoned_steps):
                new_steps_to_abandon.append(step_key)

            # If all upstream deps are good - this is executable
            elif requirements.issubset(self._success):
                new_steps_to_execute.append(step_key)

            # If some upstream deps skipped...
            elif requirements.issubset(successful_or_skipped_steps):
                step = self.get_step_by_key(step_key)

                # The base case is downstream step will skip
                should_skip = True

                # Unless a fan-in input has any successful inputs
                for inp in step.step_inputs:
                    if inp.is_from_multiple_outputs:
                        if any([key in self._success for key in inp.dependency_keys]):
                            should_skip = False

                # but no missing regular inputs
                for inp in step.step_inputs:
                    if inp.is_from_single_output:
                        if any([key not in self._success for key in inp.dependency_keys]):
                            should_skip = True

                if should_skip:
                    new_steps_to_skip.append(step_key)
                else:
                    new_steps_to_execute.append(step_key)

        for key in new_steps_to_execute:
            self._executable.append(key)
            del self._pending[key]

        for key in new_steps_to_skip:
            self._pending_skip.append(key)
            del self._pending[key]

        for key in new_steps_to_abandon:
            self._pending_abandon.append(key)
            del self._pending[key]

        ready_to_retry = []
        tick_time = time.time()
        for key, at_time in self._waiting_to_retry.items():
            if tick_time >= at_time:
                ready_to_retry.append(key)

        for key in ready_to_retry:
            self._executable.append(key)
            del self._waiting_to_retry[key]

    def sleep_til_ready(self):
        now = time.time()
        sleep_amt = min([ready_at - now for ready_at in self._waiting_to_retry.values()])
        if sleep_amt > 0:
            time.sleep(sleep_amt)

    def get_next_step(self):
        check.invariant(not self.is_complete, "Can not call get_next_step when is_complete is True")

        steps = self.get_steps_to_execute(limit=1)
        step = None

        if steps:
            step = steps[0]
        elif self._waiting_to_retry:
            self.sleep_til_ready()
            step = self.get_next_step()

        check.invariant(step is not None, "Unexpected ActiveExecution state")
        return step

    def get_step_by_key(self, step_key):
        return self._plan.get_step_by_key(step_key)

    def get_steps_to_execute(self, limit=None):
        check.invariant(
            self._context_guard, "ActiveExecution must be used as a context manager",
        )
        check.opt_int_param(limit, "limit")
        self._update()

        steps = sorted(
            [self.get_step_by_key(key) for key in self._executable], key=self._sort_key_fn
        )

        if limit:
            steps = steps[:limit]

        for step in steps:
            self._in_flight.add(step.key)
            self._executable.remove(step.key)
        return steps

    def get_steps_to_skip(self):
        self._update()

        steps = []
        steps_to_skip = list(self._pending_skip)
        for key in steps_to_skip:
            steps.append(self.get_step_by_key(key))
            self._in_flight.add(key)
            self._pending_skip.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def get_steps_to_abandon(self):
        self._update()

        steps = []
        steps_to_abandon = list(self._pending_abandon)
        for key in steps_to_abandon:
            steps.append(self.get_step_by_key(key))
            self._in_flight.add(key)
            self._pending_abandon.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def plan_events_iterator(self, pipeline_context):
        """Process all steps that can be skipped and abandoned
        """

        steps_to_skip = self.get_steps_to_skip()
        while steps_to_skip:
            for step in steps_to_skip:
                step_context = pipeline_context.for_step(step)
                skipped_inputs = []
                for step_input in step.step_inputs:
                    skipped_inputs.extend(self._skipped.intersection(step_input.dependency_keys))

                step_context.log.info(
                    "Skipping step {step} due to skipped dependencies: {skipped_inputs}.".format(
                        step=step.key, skipped_inputs=skipped_inputs
                    )
                )
                yield DagsterEvent.step_skipped_event(step_context)

                self.mark_skipped(step.key)

            steps_to_skip = self.get_steps_to_skip()

        steps_to_abandon = self.get_steps_to_abandon()
        while steps_to_abandon:
            for step in steps_to_abandon:
                step_context = pipeline_context.for_step(step)
                failed_inputs = []
                for step_input in step.step_inputs:
                    failed_inputs.extend(self._failed.intersection(step_input.dependency_keys))

                abandoned_inputs = []
                for step_input in step.step_inputs:
                    abandoned_inputs.extend(
                        self._abandoned.intersection(step_input.dependency_keys)
                    )

                step_context.log.error(
                    "Dependencies for step {step}{fail_str}{abandon_str}. Not executing.".format(
                        step=step.key,
                        fail_str=" failed: {}".format(failed_inputs) if failed_inputs else "",
                        abandon_str=" were not executed: {}".format(abandoned_inputs)
                        if abandoned_inputs
                        else "",
                    )
                )
                self.mark_abandoned(step.key)

            steps_to_abandon = self.get_steps_to_abandon()

    def mark_failed(self, step_key):
        self._failed.add(step_key)
        self._mark_complete(step_key)

    def mark_success(self, step_key):
        self._success.add(step_key)
        self._mark_complete(step_key)

    def mark_skipped(self, step_key):
        self._skipped.add(step_key)
        self._mark_complete(step_key)

    def mark_abandoned(self, step_key):
        self._abandoned.add(step_key)
        self._mark_complete(step_key)

    def mark_interrupted(self, step_key):
        self._interrupted.add(step_key)

    def check_for_interrupts(self):
        return pop_delayed_interrupts()

    def mark_up_for_retry(self, step_key, at_time=None):
        check.invariant(
            not self._retries.disabled,
            "Attempted to mark {} as up for retry but retries are disabled".format(step_key),
        )
        check.opt_float_param(at_time, "at_time")

        # if retries are enabled - queue this back up
        if self._retries.enabled:
            if at_time:
                self._waiting_to_retry[step_key] = at_time
            else:
                self._pending[step_key] = self._plan.execution_deps()[step_key]

        elif self._retries.deferred:
            # do not attempt to execute again
            self._abandoned.add(step_key)

        self._retries.mark_attempt(step_key)

        self._mark_complete(step_key)

    def _mark_complete(self, step_key):
        check.invariant(
            step_key in self._in_flight,
            "Attempted to mark step {} as complete that was not known to be in flight".format(
                step_key
            ),
        )
        self._in_flight.remove(step_key)

    def handle_event(self, dagster_event):
        check.inst_param(dagster_event, "dagster_event", DagsterEvent)

        if dagster_event.is_step_failure:
            self.mark_failed(dagster_event.step_key)
        elif dagster_event.is_step_success:
            self.mark_success(dagster_event.step_key)
        elif dagster_event.is_step_skipped:
            self.mark_skipped(dagster_event.step_key)
        elif dagster_event.is_step_up_for_retry:
            self.mark_up_for_retry(
                dagster_event.step_key,
                time.time() + dagster_event.step_retry_data.seconds_to_wait
                if dagster_event.step_retry_data.seconds_to_wait
                else None,
            )

    def verify_complete(self, pipeline_context, step_key):
        """Ensure that a step has reached a terminal state, if it has not mark it as an unexpected failure
        """
        if step_key in self._in_flight:
            if step_key in self._interrupted:
                pipeline_context.log.error(
                    "Step {key} did not complete due to being interrupted.".format(key=step_key)
                )
                self.mark_abandoned(step_key)
            else:
                pipeline_context.log.error(
                    "Step {key} finished without success or failure event. Downstream steps will not execute.".format(
                        key=step_key
                    )
                )
                self.mark_unknown_state(step_key)

    # factored out for test
    def mark_unknown_state(self, step_key):
        # note the step so that we throw upon plan completion
        self._unknown_state.add(step_key)
        # mark as abandoned so downstream tasks do not execute
        self.mark_abandoned(step_key)

    @property
    def is_complete(self):
        return (
            len(self._pending) == 0
            and len(self._in_flight) == 0
            and len(self._executable) == 0
            and len(self._pending_skip) == 0
            and len(self._pending_retry) == 0
            and len(self._pending_abandon) == 0
            and len(self._waiting_to_retry) == 0
        )
