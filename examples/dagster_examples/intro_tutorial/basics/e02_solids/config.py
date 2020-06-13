import csv
import os

from dagster import (
    Bool,
    Field,
    Int,
    String,
    execute_pipeline,
    pipeline,
    solid,
)


@solid(
    config_schema={
        'delimiter': Field(
            String,
            default_value=',',
            is_required=False,
            description=('A one-character string used to separate fields.'),
        ),
        'doublequote': Field(
            Bool,
            default_value=False,
            is_required=False,
            description=(
                'Controls how instances of quotechar appearing inside a field '
                'should themselves be quoted. When True, the character is '
                'doubled. When False, the escapechar is used as a prefix to '
                'the quotechar.'
            ),
        ),
        'escapechar': Field(
            String,
            default_value='\\',
            is_required=False,
            description=(
                'On reading, the escapechar removes any special meaning from '
                'the following character.'
            ),
        ),
        'quotechar': Field(
            String,
            default_value='"',
            is_required=False,
            description=(
                'A one-character string used to quote fields containing '
                'special characters, such as the delimiter or quotechar, '
                'or which contain new-line characters.'
            ),
        ),
        'quoting': Field(
            Int,
            default_value=csv.QUOTE_MINIMAL,
            is_required=False,
            description=(
                'Controls when quotes should be generated by the writer and '
                'recognised by the reader. It can take on any of the '
                'csv.QUOTE_* constants'
            ),
        ),
        'skipinitialspace': Field(
            Bool,
            default_value=False,
            is_required=False,
            description=(
                'When True, whitespace immediately following the delimiter '
                'is ignored. The default is False.'
            ),
        ),
        'strict': Field(
            Bool,
            default_value=False,
            is_required=False,
            description=('When True, raise exception on bad CSV input.'),
        ),
    }
)
def read_csv(context, csv_path: str):
    csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    with open(csv_path, 'r') as fd:
        lines = [
            row
            for row in csv.DictReader(
                fd,
                delimiter=context.solid_config['delimiter'],
                doublequote=context.solid_config['doublequote'],
                escapechar=context.solid_config['escapechar'],
                quotechar=context.solid_config['quotechar'],
                quoting=context.solid_config['quoting'],
                skipinitialspace=context.solid_config['skipinitialspace'],
                strict=context.solid_config['strict'],
            )
        ]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))

    return lines


@pipeline
def config_pipeline():
    read_csv()


if __name__ == '__main__':
    run_config = {
        'solids': {
            'read_csv': {'inputs': {'csv_path': {'value': 'cereal.csv'}}}
        }
    }
    result = execute_pipeline(config_pipeline, run_config=run_config)
    assert result.success
