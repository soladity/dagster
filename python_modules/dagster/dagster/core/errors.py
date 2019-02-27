from enum import Enum

from dagster import check


class DagsterExecutionFailureReason(Enum):
    USER_CODE_ERROR = 'USER_CODE_ERROR'
    FRAMEWORK_ERROR = 'FRAMEWORK_ERROR'
    EXPECTATION_FAILURE = 'EXPECATION_FAILURE'


class DagsterError(Exception):
    @property
    def is_user_code_error(self):
        return False


class DagsterUserError(DagsterError):
    pass


class DagsterRuntimeCoercionError(DagsterError):
    '''Runtime checked faild'''


class DagsterInvalidDefinitionError(DagsterUserError):
    '''Indicates that some violation of the definition rules has been violated by the user'''


class DagsterInvariantViolationError(DagsterUserError):
    '''Indicates the user has violated a well-defined invariant that can only be deteremined
    at runtime.
    '''


class DagsterTypeError(DagsterUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''


class DagsterUserCodeExecutionError(DagsterUserError):
    '''
    This is base class for any exception that is meant to wrap an Exception
    thrown by user code. It wraps that existing user code. The original_exc_info
    argument to the ctor is meant to be a sys.exc_info at the site of constructor.

    Example:

    output_type = step.step_output_dict[output_name].runtime_type
    try:
        context.persistence_strategy.write_value(
            output_type.serialization_strategy, output['path'], result.step_output_data.value
        )
    except Exception as e:  # pylint: disable=broad-except
        raise_from(
            DagsterExecutionStepExecutionError(...)
            e,
        )

    '''

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = check.inst_param(kwargs.pop('user_exception'), 'user_exception', Exception)
        original_exc_info = check.opt_tuple_param(
            kwargs.pop('original_exc_info', None), 'original_exc_info'
        )
        super(DagsterUserCodeExecutionError, self).__init__(*args, **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info

    @property
    def is_user_code_error(self):
        return True


class DagsterExecutionStepNotFoundError(DagsterUserError):
    '''
    Generic exception used whenever a user an execution step is specified in an
    api that is consumed by higher level infrastructure (e.g. airflow integration)
    or that needs to be translated into a specific in the GraphQL domain.
    '''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterExecutionStepNotFoundError, self).__init__(*args, **kwargs)


class DagsterExecutionStepExecutionError(DagsterUserCodeExecutionError):
    '''Indicates an error occured during the body of execution step execution'''


class InvalidSubplanErrorData(object):
    def __init__(self, *args, **kwargs):
        from dagster.core.execution_plan.objects import ExecutionStep

        self.pipeline_name = check.str_param(kwargs.pop('pipeline_name'), 'pipeline_name')
        self.step_keys = check.list_param(kwargs.pop('step_keys'), 'step_keys', of_type=str)
        self.step = check.inst_param(kwargs.pop('step'), 'step', ExecutionStep)

        super(InvalidSubplanErrorData, self).__init__(*args, **kwargs)


class DagsterInvalidSubplanMissingInputError(InvalidSubplanErrorData, DagsterUserError):
    '''Indicates that user has attempted to construct an execution subplan
    that cannot be executed because the user needs to specify additional inputs.
    '''

    def __init__(self, *args, **kwargs):
        self.input_name = check.str_param(kwargs.pop('input_name'), 'input_name')
        super(DagsterInvalidSubplanMissingInputError, self).__init__(*args, **kwargs)


class DagsterInvalidSubplanOutputNotFoundError(InvalidSubplanErrorData, DagsterUserError):
    def __init__(self, *args, **kwargs):
        self.output_name = check.str_param(kwargs.pop('output_name'), 'output_name')
        super(DagsterInvalidSubplanOutputNotFoundError, self).__init__(*args, **kwargs)


class DagsterInvalidSubplanInputNotFoundError(InvalidSubplanErrorData, DagsterUserError):
    def __init__(self, *args, **kwargs):
        self.input_name = check.str_param(kwargs.pop('input_name'), 'input_name')
        super(DagsterInvalidSubplanInputNotFoundError, self).__init__(*args, **kwargs)


class DagsterExpectationFailedError(DagsterError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, expectation_context, value, *args, **kwargs):
        super(DagsterExpectationFailedError, self).__init__(*args, **kwargs)
        self.expectation_context = expectation_context
        self.value = value

    def __repr__(self):
        inout_def = self.expectation_context.inout_def
        return (
            'DagsterExpectationFailedError(solid={solid_name}, {key}={inout_name}, '
            'expectation={e_name}, value={value})'
        ).format(
            solid_name=self.expectation_context.solid.name,
            key=inout_def.descriptive_key,
            inout_name=inout_def.name,
            e_name=self.expectation_context.expectation_def.name,
            value=repr(self.value),
        )

    def __str__(self):
        return self.__repr__()


class DagsterSubprocessExecutionError(DagsterError):
    '''Indicates that an error was encountered when executing part or all of an execution plan
    in a subprocess.
    
    Although this may be a user error, it is intended to be raised in circumstances where we don't
    have access to the sys.exc_info generated by the error (or where the error is raised by a 
    non-Python process).
    '''
