from dagster import Dict, Field, Int, List, Optional, PipelineDefinition, String, solid
from dagster.core.types.config.field import resolve_to_config_type
from dagster.core.types.config.type_printer import print_type_to_string


def assert_inner_types(parent_type, *dagster_types):
    assert set(
        list(map(lambda t: t.name, resolve_to_config_type(parent_type).recursive_config_types))
    ) == set(map(lambda x: x.name, map(resolve_to_config_type, dagster_types)))


def test_basic_type_print():
    assert print_type_to_string(Int) == 'Int'
    assert_inner_types(Int)


def test_basic_list_type_print():
    assert print_type_to_string(List[Int]) == '[Int]'
    assert_inner_types(List[Int], Int)


def test_double_list_type_print():
    assert print_type_to_string(List[List[Int]]) == '[[Int]]'
    int_list = List[Int]
    list_int_list = List[int_list]
    assert_inner_types(list_int_list, Int, int_list)


def test_basic_nullable_type_print():
    assert print_type_to_string(Optional[Int]) == 'Int?'
    nullable_int = Optional[Int]
    assert_inner_types(nullable_int, Int)


def test_nullable_list_combos():
    assert print_type_to_string(List[Int]) == '[Int]'
    assert print_type_to_string(Optional[List[Int]]) == '[Int]?'
    assert print_type_to_string(List[Optional[Int]]) == '[Int?]'
    assert print_type_to_string(Optional[List[Optional[Int]]]) == '[Int?]?'


def test_basic_dict():
    output = print_type_to_string(Dict({'int_field': Int}))

    expected = '''{
  int_field: Int
}'''

    assert output == expected


def test_two_field_dicts():
    two_field_dict = Dict({'int_field': Int, 'string_field': Field(String)})
    assert_inner_types(two_field_dict, Int, String)

    output = print_type_to_string(two_field_dict)

    expected = '''{
  int_field: Int
  string_field: String
}'''

    assert output == expected


def test_two_field_dicts_same_type():
    two_field_dict = Dict({'int_field1': Int, 'int_field2': Int})
    assert_inner_types(two_field_dict, Int)

    output = print_type_to_string(two_field_dict)

    expected = '''{
  int_field1: Int
  int_field2: Int
}'''

    assert output == expected


def test_optional_field():
    output = print_type_to_string(Dict({'int_field': Field(Int, is_optional=True)}))

    expected = '''{
  int_field?: Int
}'''

    assert output == expected


def test_single_level_dict_lists_and_nullable():
    output = print_type_to_string(
        Dict(
            {
                'nullable_int_field': Field(Optional[Int]),
                'optional_int_field': Field(Int, is_optional=True),
                'string_list_field': Field(List[String]),
            }
        )
    )

    expected = '''{
  nullable_int_field: Int?
  optional_int_field?: Int
  string_list_field: [String]
}'''

    assert output == expected


def test_nested_dict():
    nested_type = Dict({'int_field': Int})
    outer_type = Dict({'nested': Field(nested_type)})
    output = print_type_to_string(outer_type)

    assert_inner_types(outer_type, Int, nested_type)

    expected = '''{
  nested: {
    int_field: Int
  }
}'''

    assert output == expected


def test_test_type_pipeline_construction():
    assert define_test_type_pipeline()


def define_solid_for_test_type(name, config):
    @solid(name=name, config=config, input_defs=[], output_defs=[])
    def a_solid(_):
        return None

    return a_solid


# launch in dagit with this command:
# dagit -f test_type_printer.py -n define_test_type_pipeline
def define_test_type_pipeline():
    return PipelineDefinition(
        name='test_type_pipeline',
        solid_defs=[
            define_solid_for_test_type('int_config', Int),
            define_solid_for_test_type('list_of_int_config', List[Int]),
            define_solid_for_test_type('nullable_list_of_int_config', Optional[List[Int]]),
            define_solid_for_test_type('list_of_nullable_int_config', List[Optional[Int]]),
            define_solid_for_test_type(
                'nullable_list_of_nullable_int_config', Optional[List[Optional[Int]]]
            ),
            define_solid_for_test_type('simple_dict', {'int_field': Int, 'string_field': String}),
            define_solid_for_test_type(
                'dict_with_optional_field',
                {
                    'nullable_int_field': Optional[Int],
                    'optional_int_field': Field(Int, is_optional=True),
                    'string_list_field': List[String],
                },
            ),
            define_solid_for_test_type('nested_dict', {'nested': {'int_field': Int}}),
        ],
    )
