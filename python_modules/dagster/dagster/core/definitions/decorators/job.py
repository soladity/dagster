from dagster import check
from dagster.core.definitions.job import JobDefinition
from dagster.utils.backcompat import experimental


@experimental
def job(
    pipeline_name, name=None, mode="default", solid_selection=None, tags_fn=None,
):
    """
    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.JobDefinition` and should take a
    :py:class:`~dagster.JobContext` as its only argument, returning the run config dict for
    the pipeline execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute.
        name (Optional[str]): The name of this job.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) for the pipeline execution e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode to apply for the pipeline execution
            (Default: 'default')
        tags_fn (Optional[Callable[[JobContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the pipeline execution. Takes a
            :py:class:`~dagster.JobContext` and returns a dictionary of tags (string
            key-value pairs).
    """

    check.str_param(pipeline_name, "pipeline_name")
    check.opt_str_param(name, "name")
    check.str_param(mode, "mode")
    check.opt_nullable_list_param(solid_selection, "solid_selection", of_type=str)
    check.opt_callable_param(tags_fn, "tags_fn")

    def inner(fn):
        check.callable_param(fn, "fn")
        job_name = name or fn.__name__

        return JobDefinition(
            name=job_name,
            pipeline_name=pipeline_name,
            run_config_fn=fn,
            tags_fn=tags_fn,
            mode=mode,
            solid_selection=solid_selection,
        )

    return inner
