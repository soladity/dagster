import inspect
from contextlib import ExitStack
from typing import Any, Callable, Generator, List, NamedTuple, Optional, Union, cast

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance import DagsterInstance
from dagster.core.instance.ref import InstanceRef
from dagster.serdes import whitelist_for_serdes
from dagster.utils import ensure_gen
from dagster.utils.backcompat import experimental_arg_warning, experimental_fn_warning

from .graph import GraphDefinition
from .mode import DEFAULT_MODE_NAME
from .run_request import JobType, RunRequest, SkipReason
from .target import DirectTarget, RepoRelativeTarget
from .utils import check_valid_name

DEFAULT_SENSOR_DAEMON_INTERVAL = 30


class SensorExecutionContext:
    """Sensor execution context.

    An instance of this class is made available as the first argument to the evaluation function
    on SensorDefinition.

    Attributes:
        instance_ref (Optional[InstanceRef]): The serialized instance configured to run the schedule
        cursor (Optional[str]): The cursor, passed back from the last sensor evaluation via
            the cursor attribute of SkipReason and RunRequest
        last_completion_time (float): DEPRECATED The last time that the sensor was evaluated (UTC).
        last_run_key (str): DEPRECATED The run key of the RunRequest most recently created by this
            sensor. Use the preferred `cursor` attribute instead.
    """

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
    ):
        self._exit_stack = ExitStack()
        self._instance = None

        self._instance_ref = check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        self._last_completion_time = check.opt_float_param(
            last_completion_time, "last_completion_time"
        )
        self._last_run_key = check.opt_str_param(last_run_key, "last_run_key")
        self._cursor = check.opt_str_param(cursor, "cursor")

        self._instance = None

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

    @property
    def instance(self) -> DagsterInstance:
        # self._instance_ref should only ever be None when this SensorExecutionContext was
        # constructed under test.
        if not self._instance_ref:
            raise DagsterInvariantViolationError(
                "Attempted to initialize dagster instance, but no instance reference was provided."
            )
        if not self._instance:
            self._instance = self._exit_stack.enter_context(
                DagsterInstance.from_ref(self._instance_ref)
            )
        return cast(DagsterInstance, self._instance)

    @property
    def last_completion_time(self) -> Optional[float]:
        return self._last_completion_time

    @property
    def last_run_key(self) -> Optional[str]:
        return self._last_run_key

    @property
    def cursor(self) -> Optional[str]:
        """The cursor value for this sensor, which was set in an earlier sensor evaluation."""
        return self._cursor

    def update_cursor(self, cursor: Optional[str]) -> None:
        """Updates the cursor value for this sensor, which will be provided on the context for the
        next sensor evaluation.

        This can be used to keep track of progress and avoid duplicate work across sensor
        evaluations.

        Args:
            cursor (Optional[str]):
        """
        self._cursor = check.opt_str_param(cursor, "cursor")


class SensorDefinition:
    """Define a sensor that initiates a set of runs based on some external state

    Args:
        name (str): The name of the sensor to create.
        pipeline_name (str): The name of the pipeline to execute when the sensor fires.
        evaluation_fn (Callable[[SensorExecutionContext]]): The core evaluation function for the
            sensor, which is run at an interval to determine whether a run should be launched or
            not. Takes a :py:class:`~dagster.SensorExecutionContext`.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the sensor runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing runs triggered by this sensor.
            (default: 'default')
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[PipelineDefinition]): Experimental
    """

    def __init__(
        self,
        name: str,
        pipeline_name: Optional[str],
        evaluation_fn: Callable[
            ["SensorExecutionContext"],
            Union[Generator[Union[RunRequest, SkipReason], None, None], RunRequest, SkipReason],
        ],
        solid_selection: Optional[List[Any]] = None,
        mode: Optional[str] = None,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[GraphDefinition] = None,
    ):

        self._name = check_valid_name(name)

        if job is not None:
            experimental_arg_warning("target", "SensorDefinition.__init__")
            self._target: Union[DirectTarget, RepoRelativeTarget] = DirectTarget(job)
        else:
            self._target = RepoRelativeTarget(
                pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
                mode=check.opt_str_param(mode, "mode") or DEFAULT_MODE_NAME,
                solid_selection=check.opt_nullable_list_param(
                    solid_selection, "solid_selection", of_type=str
                ),
            )

        self._description = check.opt_str_param(description, "description")
        self._evaluation_fn = check.callable_param(evaluation_fn, "evaluation_fn")
        self._min_interval = check.opt_int_param(
            minimum_interval_seconds, "minimum_interval_seconds", DEFAULT_SENSOR_DAEMON_INTERVAL
        )

    # This allows us to pass sensor definition off as a function, so that it can inherit the
    # metadata of the wrapped function.
    def __call__(self, *args, **kwargs):
        return self

    @property
    def name(self) -> str:
        return self._name

    @property
    def pipeline_name(self) -> str:
        return self._target.pipeline_name

    @property
    def job_type(self) -> JobType:
        return JobType.SENSOR

    @property
    def solid_selection(self) -> Optional[List[Any]]:
        return self._target.solid_selection

    @property
    def mode(self) -> Optional[str]:
        return self._target.mode

    @property
    def description(self) -> Optional[str]:
        return self._description

    def evaluate_tick(self, context: "SensorExecutionContext") -> "SensorExecutionData":
        """Evaluate sensor using the provided context.

        Args:
            context (SensorExecutionContext): The context with which to evaluate this sensor.
        Returns:
            SensorExecutionData: Contains list of run requests, or skip message if present.

        """

        check.inst_param(context, "context", SensorExecutionContext)
        result = list(ensure_gen(self._evaluation_fn(context)))

        if not result or result == [None]:
            run_requests = []
            skip_message = None
        elif len(result) == 1:
            item = result[0]
            check.inst(item, (SkipReason, RunRequest))
            run_requests = [item] if isinstance(item, RunRequest) else []
            skip_message = item.skip_message if isinstance(item, SkipReason) else None
        else:
            check.is_list(result, of_type=RunRequest)
            run_requests = result
            skip_message = None

        return SensorExecutionData(run_requests, skip_message, context.cursor)

    @property
    def minimum_interval_seconds(self) -> Optional[int]:
        return self._min_interval

    def has_loadable_target(self):
        return isinstance(self._target, DirectTarget)

    def load_target(self):
        if isinstance(self._target, DirectTarget):
            return self._target.load()

        check.failed("Target is not loadable")


@whitelist_for_serdes
class SensorExecutionData(
    NamedTuple(
        "_SensorExecutionData",
        [
            ("run_requests", Optional[List[RunRequest]]),
            ("skip_message", Optional[str]),
            ("cursor", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        run_requests: Optional[List[RunRequest]] = None,
        skip_message: Optional[str] = None,
        cursor: Optional[str] = None,
    ):
        check.opt_list_param(run_requests, "run_requests", RunRequest)
        check.opt_str_param(skip_message, "skip_message")
        check.opt_str_param(cursor, "cursor")
        check.invariant(
            not (run_requests and skip_message), "Found both skip data and run request data"
        )
        return super(SensorExecutionData, cls).__new__(
            cls,
            run_requests=run_requests,
            skip_message=skip_message,
            cursor=cursor,
        )


def wrap_sensor_evaluation(
    sensor_name: str,
    result: Union[Generator[Union[SkipReason, RunRequest], None, None], SkipReason, RunRequest],
) -> Generator[Union[SkipReason, RunRequest], None, None]:
    if inspect.isgenerator(result):
        for item in result:
            yield item

    elif isinstance(result, (SkipReason, RunRequest)):
        yield result

    elif result is not None:
        raise DagsterInvariantViolationError(
            f"Error in sensor {sensor_name}: Sensor unexpectedly returned output "
            f"{result} of type {type(result)}.  Should only return SkipReason or "
            "RunRequest objects."
        )


def build_sensor_context(
    instance: Optional[DagsterInstance] = None, cursor: Optional[str] = None
) -> SensorExecutionContext:
    """Builds sensor execution context using the provided parameters.

    If provided, the dagster instance must be persistent;
    DagsterInstance.ephemeral() will result in an error.

    Args:
        instance (Optional[DagsterInstance]): The dagster instance configured to run the sensor.
        cursor (Optional[str]): A cursor value to provide to the evaluation of the sensor.

    Examples:

        .. code-block:: python

            context = build_sensor_context()
            my_sensor.evaluate_tick(context)

    """

    experimental_fn_warning("build_sensor_context")

    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(cursor, "cursor")
    return SensorExecutionContext(
        instance_ref=instance.get_ref() if instance else None,
        last_completion_time=None,
        last_run_key=None,
        cursor=cursor,
    )
