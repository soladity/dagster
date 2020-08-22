from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError


class HookDefinition(namedtuple("_HookDefinition", "name hook_fn required_resource_keys")):
    """Define a hook which can be triggered during a solid execution (e.g. a callback on the step
    execution failure event during a solid execution).

    Args:
        name (str): The name of this hook.
        hook_fn (Callable): The callback function that will be triggered.
        required_resource_keys (Optional[Set[str]]): Keys for the resources required by the
            hook.
    """

    def __new__(cls, name, hook_fn, required_resource_keys=None):
        return super(HookDefinition, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            hook_fn=check.callable_param(hook_fn, "hook_fn"),
            required_resource_keys=frozenset(
                check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
            ),
        )

    def __call__(self, obj):
        """This is invoked when the hook is used as a decorator.

        We currently support hooks to decorate the following:

        - PipelineDefinition: when the hook decorates a pipeline definition, it will be added to
            all the solid invocations within the pipeline.

        Example:
            .. code-block:: python

                @success_hook
                def slack_on_success(_):
                    ...

                @slack_on_success
                @pipeline
                def a_pipeline():
                    foo(bar())

        """

        from .pipeline import PipelineDefinition

        if isinstance(obj, PipelineDefinition):
            # when it decorates a pipeline, we apply this hook to all the solid invocations within
            # the pipeline.
            return obj.with_hooks({self})
        else:
            raise DagsterInvalidDefinitionError(
                (
                    'Hook "{hook_name}" should decorate a pipeline definition, '
                    "or be applied on a solid invocation."
                ).format(hook_name=self.name)
            )
