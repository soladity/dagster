import sys

from dagster.core.types import Bool, Float, Int, PythonDict, String

from .wrapping import (
    is_closed_python_optional_typehint,
    is_python_list_typehint,
    remap_to_dagster_list_type,
    remap_to_dagster_optional_type,
)


def remap_python_type(type_annotation):

    if type_annotation == int:
        return Int
    if type_annotation == float:
        return Float
    if type_annotation == bool:
        return Bool
    if type_annotation == str:
        return String
    if type_annotation == dict:
        return PythonDict

    if sys.version_info.major >= 3:
        if is_python_list_typehint(type_annotation):
            return remap_to_dagster_list_type(type_annotation)
        if is_closed_python_optional_typehint(type_annotation):
            return remap_to_dagster_optional_type(type_annotation)

    return type_annotation
