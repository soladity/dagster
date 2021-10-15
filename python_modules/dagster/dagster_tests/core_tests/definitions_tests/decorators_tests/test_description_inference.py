from dagster import composite_solid, graph, job, op, solid


def test_description_inference():
    decorators = [job, op, graph, solid, composite_solid]
    for decorator in decorators:

        @decorator
        def my_thing():
            """
            Here is some
            multiline description.
            """

        assert my_thing.description == "\n".join(["Here is some", "multiline description."])
