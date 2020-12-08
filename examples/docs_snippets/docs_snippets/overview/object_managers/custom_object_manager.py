"""isort:skip_file"""
from dagster import solid


@solid
def solid1(_):
    pass


@solid
def solid2(_, _a):
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# start_marker
from dagster import ObjectManager, ModeDefinition, object_manager, pipeline


class DataframeTableObjectManager(ObjectManager):
    def handle_output(self, context, obj):
        # name is the name given to the OutputDefinition that we're storing for
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        # upstream_output.name is the name given to the OutputDefinition that we're loading for
        table_name = context.upstream_output.name
        return read_dataframe_from_table(name=table_name)


@object_manager
def df_table_object_manager(_):
    return DataframeTableObjectManager()


@pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": df_table_object_manager})])
def my_pipeline():
    solid2(solid1())


# end_marker
