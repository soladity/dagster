from collections import defaultdict, namedtuple
from dagster import check

from .marshal import create_unmarshal_input_step, create_marshal_output_step
from .utility import create_value_thunk_step


class ExecutionPlanSubsetInfo(
    namedtuple('_ExecutionPlanSubsetInfo', 'subset input_step_factory_fns')
):
    '''
    ExecutionPlanSubsetInfo is created in order to build subset of an execution plan. If
    the caller has removed execution steps from the plan that provide outputs to downstream
    steps, they must somehow provide new values. In order to make this facility generic,
    the interface that this object provides to the guts to the execution engine is a set
    of functions that create ExecutionSteps, indexed by step key and input name. When
    the execution creation plan process needs an input and it is not in the subset
    provided, it instead calls this function to create the execution step.

    Callers of create_execution_plan and similar should use the static method functions
    which provide handy, easier-to-use functions that manage this callback creation
    process.
    '''

    @staticmethod
    def only_subset(included_step_keys):
        ''' Creates a subset with no injected steps at all.'''
        return ExecutionPlanSubsetInfo(included_step_keys, {})

    @staticmethod
    def with_input_values(included_step_keys, inputs):
        '''
        Create an execution subset with hardcoded values as inputs. This will create
        execution steps with the key "{step_key}.input.{input_name}.value" that simply
        emit the value

        inputs dictionary is a Dict[str,Dict[str,Any]] mapping

        step_key => input_name => value

        Example:

        create_execution_plan(
            define_two_int_pipeline(),
            subset_info=ExecutionPlanSubsetInfo.with_input_values(
                ['add_one.transform'], {'add_one.transform': {'num': 2}}
            ),
        )

        '''
        check.list_param(included_step_keys, 'included_step_keys', of_type=str)
        check.two_dim_dict_param(inputs, 'inputs', key_type=str)

        def _create_injected_value_factory_fn(input_value):
            return lambda pipeline_context, step, step_input: create_value_thunk_step(
                pipeline_context=pipeline_context,
                solid=step.solid,
                runtime_type=step_input.runtime_type,
                step_key='{step_key}.input.{input_name}.value'.format(
                    step_key=step.key, input_name=step_input.name
                ),
                value=input_value,
            )

        input_step_factory_fns = defaultdict(dict)
        for step_key, input_dict in inputs.items():
            for input_name, input_value in input_dict.items():
                input_step_factory_fns[step_key][input_name] = _create_injected_value_factory_fn(
                    input_value
                )

        return ExecutionPlanSubsetInfo(included_step_keys, input_step_factory_fns)

    @staticmethod
    def with_input_marshalling(included_step_keys, marshalled_inputs=None):
        '''
        Create an execution subset that uses the marshalling infrastruture in order
        to provide values to includes.

        inputs dictionary is a Dict[str,Dict[str,Any]] mapping

        step_key => input_name => marshalling_key
        '''
        check.list_param(included_step_keys, 'included_step_keys', of_type=str)
        marshalled_inputs = check.opt_two_dim_dict_param(marshalled_inputs, 'marshalled_inputs')

        input_step_factory_fns = defaultdict(dict)

        def _create_unmarshal_input_factory_fn(marshalling_key):
            return lambda pipeline_context, step, step_input: create_unmarshal_input_step(
                pipeline_context, step, step_input, marshalling_key
            )

        for step_key, input_marshal_dict in marshalled_inputs.items():
            for input_name, key in input_marshal_dict.items():
                input_step_factory_fns[step_key][input_name] = _create_unmarshal_input_factory_fn(
                    key
                )

        return ExecutionPlanSubsetInfo(included_step_keys, input_step_factory_fns)

    def has_injected_step_for_input(self, step_key, input_name):
        check.str_param(step_key, 'step_key')
        check.str_param(input_name, 'input_name')
        return (
            step_key in self.input_step_factory_fns
            and input_name in self.input_step_factory_fns[step_key]
        )

    def __new__(cls, included_step_keys, input_step_factory_fns):
        '''
            This should not be called directly, but instead through the static methods
            on this class.

            included_step_keys: list of step keys to include in the subset

            input_step_factory_fns: A 2D dictinoary step_key => input_name => callable

            callable should have signature of

            (StepBuilderState, ExecutionStep, StepInput): StepOutputHandle

            Full type signature is
            Dict[str,
                Dict[str,
                    Callable[StepBuilderState, ExecutionStep, StepInput]: StepOutputHandle
                ]
            ]
        '''

        return super(ExecutionPlanSubsetInfo, cls).__new__(
            cls,
            set(check.list_param(included_step_keys, 'included_step_keys', of_type=str)),
            check.opt_two_dim_dict_param(
                input_step_factory_fns, 'input_step_factory_fns', key_type=str
            ),
        )


class MarshalledOutput(namedtuple('_MarshalledOutput', 'output_name marshalling_key')):
    def __new__(cls, output_name, marshalling_key):
        return super(MarshalledOutput, cls).__new__(
            cls,
            check.str_param(output_name, 'output_name'),
            check.str_param(marshalling_key, 'marshalling_key'),
        )


MarshalledInput = namedtuple('MarshalledInput', 'input_name key')


class StepExecution(namedtuple('_StepExecution', 'step_key marshalled_inputs marshalled_outputs')):
    def __new__(cls, step_key, marshalled_inputs, marshalled_outputs):
        return super(StepExecution, cls).__new__(
            cls,
            check.str_param(step_key, 'step_key'),
            check.list_param(marshalled_inputs, 'marshalled_inputs', of_type=MarshalledInput),
            check.list_param(marshalled_outputs, 'marshalled_outputs', of_type=MarshalledOutput),
        )


class OutputStepFactoryEntry(namedtuple('_OutputStepFactoryEntry', 'output_name step_factory_fn')):
    def __new__(cls, output_name, step_factory_fn):
        return super(OutputStepFactoryEntry, cls).__new__(
            cls,
            check.str_param(output_name, 'output_name'),
            check.callable_param(step_factory_fn, 'step_factory_fn'),
        )


class ExecutionPlanAddedOutputs(
    namedtuple('_ExecutionPlanAddedOutputs', 'output_step_factory_fns')
):
    def __new__(cls, output_step_factory_fns):
        check.dict_param(
            output_step_factory_fns, 'output_step_factory_fns', key_type=str, value_type=list
        )
        for step_factory_fns_for_output in output_step_factory_fns.values():
            check.list_param(
                step_factory_fns_for_output,
                'output_step_factory_fns',
                of_type=OutputStepFactoryEntry,
            )

        return super(ExecutionPlanAddedOutputs, cls).__new__(cls, output_step_factory_fns)

    @staticmethod
    def with_output_marshalling(marshalled_outputs):
        marshalled_outputs = check.opt_dict_param(
            marshalled_outputs, 'marshalled_outputs', key_type=str
        )

        for outputs_for_step in marshalled_outputs.values():
            check.list_param(outputs_for_step, 'outputs_for_step', of_type=MarshalledOutput)

        output_step_factory_fns = defaultdict(list)

        def _create_marshal_output_fn(key):
            return lambda pipeline_context, step, step_output: create_marshal_output_step(
                pipeline_context, step, step_output, key
            )

        for step_key, outputs_for_step in marshalled_outputs.items():
            for marshalled_output in outputs_for_step:
                # for every marshalled output passed in, create a new fn that returns
                # a step that performs the marshalling

                output_step_factory_fns[step_key].append(
                    OutputStepFactoryEntry(
                        output_name=marshalled_output.output_name,
                        step_factory_fn=_create_marshal_output_fn(
                            marshalled_output.marshalling_key
                        ),
                    )
                )

        return ExecutionPlanAddedOutputs(output_step_factory_fns)
