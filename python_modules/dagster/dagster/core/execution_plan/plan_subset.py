from collections import defaultdict, namedtuple
from dagster import check
from dagster.core.definitions.utils import check_opt_two_dim_dict
from .objects import StepBuilderState, ExecutionStep, StepInput
from .utility import create_value_thunk_step


class ExecutionPlanSubsetInfo(namedtuple('_ExecutionPlanSubsetInfo', 'subset step_factory_fns')):
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
        '''
        check.list_param(included_step_keys, 'included_step_keys', of_type=str)
        check_opt_two_dim_dict(inputs, 'inputs', key_type=str)

        def _create_injected_value_factory_fn(input_value):
            def _injected_value_factory_fn(state, step, step_input):
                check.inst_param(state, 'state', StepBuilderState)
                check.inst_param(step, 'step', ExecutionStep)
                check.inst_param(step_input, 'step_input', StepInput)
                return create_value_thunk_step(
                    state=state,
                    solid=step.solid,
                    runtime_type=step_input.runtime_type,
                    step_key='{step_key}.input.{input_name}.value'.format(
                        step_key=step.key, input_name=step_input.name
                    ),
                    value=input_value,
                )

            return _injected_value_factory_fn

        step_factory_fns = defaultdict(dict)
        for step_key, input_dict in inputs.items():
            for input_name, input_value in input_dict.items():
                factory_fn = _create_injected_value_factory_fn(input_value)
                step_factory_fns[step_key][input_name] = factory_fn

        return ExecutionPlanSubsetInfo(included_step_keys, step_factory_fns)

    def has_injected_step(self, step_key, input_name):
        check.str_param(step_key, 'step_key')
        check.str_param(input_name, 'input_name')
        return step_key in self.step_factory_fns and input_name in self.step_factory_fns[step_key]

    def __new__(cls, included_step_keys, step_factory_fns):
        '''
            This should not be called directly, but instead through the static methods
            on this class.

            included_step_keys: list of step keys to include in the subset

            step_factory_fns: A 2D dictinoary step_key => input_name => callable

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
            check_opt_two_dim_dict(step_factory_fns, 'step_factory_fns', key_type=str),
        )
