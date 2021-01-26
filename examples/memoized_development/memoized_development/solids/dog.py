from dagster import solid
from memoized_development.solids.solid_utils import get_hash_for_file


@solid(version=get_hash_for_file(__file__), config_schema={"dog_breed": str})
def emit_dog(context):
    breed = context.solid_config["dog_breed"]
    return breed
