from __future__ import absolute_import

import abc
import atexit
import copy
import logging
import os
import sys
import time
from collections import namedtuple

import gevent
import six

from dagster import (
    ExecutionTargetHandle,
    PipelineDefinition,
    PipelineExecutionResult,
    RunConfig,
    check,
    execute_pipeline_iterator,
)
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    PipelineProcessStartData,
    PipelineProcessStartedData,
)
from dagster.core.events.log import DagsterEventRecord
from dagster.utils import get_multiprocessing_context
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster.core.events import CallbackEventSink
from dagster_graphql.implementation.pipeline_run_storage import PipelineRun


class PipelineExecutionManager(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def execute_pipeline(self, handle, pipeline, pipeline_run, raise_on_error):
        '''Subclasses must implement this method.'''


def build_synthetic_pipeline_error_record(run_id, error_info, pipeline_name):
    check.str_param(run_id, 'run_id')
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(error_info, 'error_info', SerializableErrorInfo)

    return DagsterEventRecord(
        message=error_info.message + '\nStack Trace:\n' + '\n'.join(error_info.stack),
        # Currently it is the user_message that is displayed to the user client side
        # in dagit even though that was not the original intent. The original
        # intent was that the user_message was the message generated by user code
        # communicated directly to the client. We need to rationalize the treatment
        # of these different error messages
        user_message=(
            'An exception was thrown during execution that is likely a framework error, '
            'rather than an error in user code.'
        )
        + '\nOriginal error message: '
        + error_info.message
        + '\nStack Trace:\n'
        + '\n'.join(error_info.stack),
        level=logging.ERROR,
        run_id=run_id,
        timestamp=time.time(),
        error_info=error_info,
        pipeline_name=pipeline_name,
        dagster_event=DagsterEvent(DagsterEventType.PIPELINE_FAILURE.value, pipeline_name),
    )


def build_process_start_event(run_id, pipeline_name):
    check.str_param(pipeline_name, 'pipeline_name')
    check.str_param(run_id, 'run_id')
    message = 'About to start process for pipeline "{pipeline_name}" (run_id: {run_id}).'.format(
        pipeline_name=pipeline_name, run_id=run_id
    )

    return DagsterEventRecord(
        message=message,
        user_message=message,
        level=logging.INFO,
        run_id=run_id,
        timestamp=time.time(),
        error_info=None,
        pipeline_name=pipeline_name,
        dagster_event=DagsterEvent(
            message=message,
            event_type_value=DagsterEventType.PIPELINE_PROCESS_START.value,
            pipeline_name=pipeline_name,
            event_specific_data=PipelineProcessStartData(pipeline_name, run_id),
        ),
    )


def build_process_started_event(run_id, pipeline_name, process_id):
    message = 'Started process for pipeline (pid: {process_id}).'.format(process_id=process_id)

    return DagsterEventRecord(
        message=message,
        user_message=message,
        level=logging.INFO,
        run_id=run_id,
        timestamp=time.time(),
        error_info=None,
        pipeline_name=pipeline_name,
        dagster_event=DagsterEvent(
            message=message,
            event_type_value=DagsterEventType.PIPELINE_PROCESS_STARTED.value,
            pipeline_name=pipeline_name,
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
            event_specific_data=PipelineProcessStartedData(
                pipeline_name=pipeline_name, run_id=run_id, process_id=process_id
            ),
        ),
    )


class SynchronousExecutionManager(PipelineExecutionManager):
    def execute_pipeline(self, _, pipeline, pipeline_run, raise_on_error):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)

        run_config = RunConfig(
            pipeline_run.run_id,
            mode=pipeline_run.mode,
            event_sink=CallbackEventSink(pipeline_run.handle_new_event),
            reexecution_config=pipeline_run.reexecution_config,
            step_keys_to_execute=pipeline_run.step_keys_to_execute,
        )

        # We do this instead of just using execute_pipeline to avoid spurious pipeline start and
        # pipeline success or pipeline failure events.
        try:
            event_list = []
            for event in execute_pipeline_iterator(
                pipeline, pipeline_run.config, run_config=run_config
            ):
                event_list.append(event)
            return PipelineExecutionResult(pipeline, run_config.run_id, event_list, lambda: None)
        except Exception:  # pylint: disable=broad-except
            if raise_on_error:
                six.reraise(*sys.exc_info())

            pipeline_run.handle_new_event(
                build_synthetic_pipeline_error_record(
                    pipeline_run.run_id,
                    serializable_error_info_from_exc_info(sys.exc_info()),
                    pipeline.name,
                )
            )


class MultiprocessingDone(object):
    pass


class MultiprocessingError(object):
    def __init__(self, error_info):
        self.error_info = check.inst_param(error_info, 'error_info', SerializableErrorInfo)


class ProcessStartedSentinel(object):
    def __init__(self, process_id):
        self.process_id = check.int_param(process_id, 'process_id')


class MultiprocessingExecutionManager(PipelineExecutionManager):
    def __init__(self):
        self._multiprocessing_context = get_multiprocessing_context()
        self._processes_lock = self._multiprocessing_context.Lock()
        self._processes = []
        # This is actually a reverse semaphore. We keep track of number of
        # processes we have by releasing semaphore every time we start
        # processing, we acquire after processing is finished
        self._processing_semaphore = gevent.lock.Semaphore(0)

        gevent.spawn(self._start_polling)
        atexit.register(self._cleanup)

    def _start_polling(self):
        while True:
            self._poll()
            gevent.sleep(0.1)

    def _cleanup(self):
        # Wait for child processes to finish and communicate on exit
        self.join()

    def _poll(self):
        with self._processes_lock:
            processes = copy.copy(self._processes)
            self._processes = []
            for _ in processes:
                self._processing_semaphore.release()

        for process in processes:
            done = self._consume_process_queue(process)
            if not done and not process.process.is_alive():
                done = self._consume_process_queue(process)
                if not done:
                    try:
                        done = True
                        raise Exception(
                            'Pipeline execution process for {run_id} unexpectedly exited'.format(
                                run_id=process.pipeline_run.run_id
                            )
                        )
                    except Exception:  # pylint: disable=broad-except
                        process.pipeline_run.handle_new_event(
                            build_synthetic_pipeline_error_record(
                                process.pipeline_run.run_id,
                                serializable_error_info_from_exc_info(sys.exc_info()),
                                process.pipeline_run.pipeline_name,
                            )
                        )

            if not done:
                self._processes.append(process)

            self._processing_semaphore.acquire()

    def _consume_process_queue(self, process):
        while not process.message_queue.empty():
            message = process.message_queue.get(False)
            if isinstance(message, MultiprocessingDone):
                return True
            elif isinstance(message, MultiprocessingError):
                process.pipeline_run.handle_new_event(
                    build_synthetic_pipeline_error_record(
                        process.pipeline_run.run_id,
                        message.error_info,
                        process.pipeline_run.pipeline_name,
                    )
                )
            elif isinstance(message, ProcessStartedSentinel):
                process.pipeline_run.handle_new_event(
                    build_process_started_event(
                        process.pipeline_run.run_id,
                        process.pipeline_run.pipeline_name,
                        message.process_id,
                    )
                )
            else:
                process.pipeline_run.handle_new_event(message)
        return False

    def join(self):
        '''Waits until all there are no processes enqueued.'''
        while True:
            with self._processes_lock:
                if not self._processes and self._processing_semaphore.locked():
                    return True
            gevent.sleep(0.1)

    def execute_pipeline(self, handle, pipeline, pipeline_run, raise_on_error):
        check.inst_param(handle, 'handle', ExecutionTargetHandle)
        check.invariant(
            raise_on_error is False, 'Multiprocessing execute_pipeline does not rethrow user error'
        )

        message_queue = self._multiprocessing_context.Queue()
        p = self._multiprocessing_context.Process(
            target=execute_pipeline_through_queue,
            args=(
                handle,
                pipeline_run.selector.name,
                pipeline_run.selector.solid_subset,
                pipeline_run.config,
            ),
            kwargs={
                'run_id': pipeline_run.run_id,
                'mode': pipeline_run.mode,
                'message_queue': message_queue,
                'reexecution_config': pipeline_run.reexecution_config,
                'step_keys_to_execute': pipeline_run.step_keys_to_execute,
            },
        )

        pipeline_run.handle_new_event(build_process_start_event(pipeline_run.run_id, pipeline.name))

        p.start()
        with self._processes_lock:
            process = RunProcessWrapper(pipeline_run, p, message_queue)
            self._processes.append(process)


class RunProcessWrapper(namedtuple('RunProcessWrapper', 'pipeline_run process message_queue')):
    def __new__(cls, pipeline_run, process, message_queue):
        return super(RunProcessWrapper, cls).__new__(
            cls, check.inst_param(pipeline_run, 'pipeline_run', PipelineRun), process, message_queue
        )


def execute_pipeline_through_queue(
    handle,
    pipeline_name,
    solid_subset,
    environment_dict,
    mode,
    run_id,
    message_queue,
    reexecution_config,
    step_keys_to_execute,
):
    """
    Execute pipeline using message queue as a transport
    """

    check.opt_str_param(mode, 'mode')

    message_queue.put(ProcessStartedSentinel(os.getpid()))

    run_config = RunConfig(
        run_id,
        mode=mode,
        event_sink=CallbackEventSink(message_queue.put),
        reexecution_config=reexecution_config,
        step_keys_to_execute=step_keys_to_execute,
    )

    if 'execution' not in environment_dict or not environment_dict['execution']:
        environment_dict['execution'] = {'in_process': {'config': {'raise_on_error': False}}}

    try:
        handle.build_repository_definition()
        pipeline_def = handle.with_pipeline_name(pipeline_name).build_pipeline_definition()
    except Exception:  # pylint: disable=broad-except
        repo_error = sys.exc_info()
        message_queue.put(MultiprocessingError(serializable_error_info_from_exc_info(repo_error)))
        return

    try:
        event_list = []
        for event in execute_pipeline_iterator(
            pipeline_def.build_sub_pipeline(solid_subset), environment_dict, run_config=run_config
        ):
            # message_queue.put(event)
            event_list.append(event)
        return PipelineExecutionResult(pipeline_def, run_config.run_id, event_list, lambda: None)
    except Exception:  # pylint: disable=broad-except
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        message_queue.put(MultiprocessingError(error_info))
    finally:
        message_queue.put(MultiprocessingDone())
        message_queue.close()
