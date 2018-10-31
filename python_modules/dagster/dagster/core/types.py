from collections import namedtuple
import json
import os
import pickle

from six import integer_types, string_types

from dagster import check
from dagster.core.errors import DagsterEvaluateValueError

SerializedTypeValue = namedtuple('SerializedTypeValue', 'name value')


class DagsterType(object):
    '''Base class for Dagster Type system. Should be inherited by a subclass.
    Subclass must implement `evaluate_value`

    Attributes:
      name (str): Name of the type

      description (str): Description of the type
    '''

    def __init__(self, name, description=None):
        self.name = check.str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')
        self.__doc__ = description

    def __repr__(self):
        return 'DagsterType({name})'.format(name=self.name)

    def evaluate_value(self, _value):
        '''Subclasses can implement this method. Check if the value is a valid one
        and return a processed version of it. If value is invalid,
        raise `DagsterEvaluateValueError`.

        This class provides a default implementation of this method

        Args:
          value: The value to check

        Returns:
          value: A transformed value
        '''
        check.not_implemented('Must implement in subclass')

    def iterate_types(self):
        yield self

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(self.evaluate_value(value), output_dir)
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump(
                {
                    'type': type_value.name,
                    'value': type_value.value,
                },
                ff,
            )
        return type_value

    def deserialize_value(self, output_dir):
        with open(os.path.join(output_dir, 'type_value'), 'r') as ff:
            type_value_dict = json.load(ff)
            type_value = SerializedTypeValue(
                name=type_value_dict['type'],
                value=type_value_dict['value'],
            )
            if type_value.name != self.name:
                raise Exception('type mismatch')
            return self.deserialize_from_type_value(type_value, output_dir)

    # Override these in subclasses for customizable serialization
    def create_serializable_type_value(self, value, _output_dir):
        return SerializedTypeValue(self.name, value)

    # Override these in subclasses for customizable serialization
    def deserialize_from_type_value(self, type_value, _output_dir):
        return type_value.value


class UncoercedTypeMixin(object):
    '''This is a helper mixin used when you only want to do a type check
    against an in-memory value and then leave that value uncoerced. Only
    is_python_valid_value must be implemented for these classes.
    evaluate_value is implemented for you.
    '''

    def is_python_valid_value(self, _value):
        '''Subclasses must implement this method. Check if the value and output a boolean.

        Returns:
          bool: Whether the value is valid.
        '''
        check.failed('must implement')

    def evaluate_value(self, value):
        if not self.is_python_valid_value(value):
            raise DagsterEvaluateValueError(
                'Expected valid value for {type_name} but got {value}'.format(
                    type_name=self.name,
                    value=repr(value),
                )
            )
        return value


class DagsterScalarType(UncoercedTypeMixin, DagsterType):
    '''Base class for dagster types that are scalar python values.

    Attributes:
      name (str): Name of the type

      description (str): Description of the type
    '''

    def __init__(self, *args, **kwargs):
        super(DagsterScalarType, self).__init__(*args, **kwargs)


class _DagsterAnyType(UncoercedTypeMixin, DagsterType):
    def __init__(self):
        super(_DagsterAnyType, self).__init__(
            name='Any',
            description='The type that allows any value, including no value.',
        )

    def is_python_valid_value(self, _value):
        return True


def nullable_isinstance(value, typez):
    return value is None or isinstance(value, typez)


class PythonObjectType(UncoercedTypeMixin, DagsterType):
    '''Dagster Type that checks if the value is an instance of some `python_type`'''

    def __init__(
        self,
        name,
        python_type,
        description=None,
    ):
        super(PythonObjectType, self).__init__(name, description)
        self.python_type = check.type_param(python_type, 'python_type')

    def is_python_valid_value(self, value):
        return nullable_isinstance(value, self.python_type)

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(self.evaluate_value(value), output_dir)
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump(
                {
                    'type': type_value.name,
                    'path': 'pickle'
                },
                ff,
            )
        pickle_path = os.path.join(output_dir, 'pickle')
        with open(pickle_path, 'wb') as pf:
            pickle.dump(value, pf)

        return type_value

    # If python had final methods, these would be final
    def deserialize_value(self, output_dir):
        with open(os.path.join(output_dir, 'type_value'), 'r') as ff:
            type_value_dict = json.load(ff)
            if type_value_dict['type'] != self.name:
                raise Exception('type mismatch')

        path = type_value_dict['path']
        with open(os.path.join(output_dir, path), 'rb') as pf:
            return pickle.load(pf)


class DagsterStringType(DagsterScalarType):
    def is_python_valid_value(self, value):
        return nullable_isinstance(value, string_types)


class _DagsterIntType(DagsterScalarType):
    def __init__(self):
        super(_DagsterIntType, self).__init__('Int', description='An integer.')

    def is_python_valid_value(self, value):
        if isinstance(value, bool):
            return False
        return nullable_isinstance(value, integer_types)


class _DagsterBoolType(DagsterScalarType):
    def __init__(self):
        super(_DagsterBoolType, self).__init__('Bool', description='A boolean.')

    def is_python_valid_value(self, value):
        return nullable_isinstance(value, bool)


class __FieldValueSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel


class Field:
    '''
    A Field in a DagsterCompositeType.

    Attributes:
        dagster_type (DagsterType): The type of the field.
        default_value (Any):
            If the Field is optional, a default value can be provided when the field value
            is not specified.
        is_optional (bool): Is the field optional.
        description (str): Description of the field.
    '''

    def __init__(
        self,
        dagster_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=False,
        description=None
    ):
        if not is_optional:
            check.param_invariant(
                default_value == FIELD_NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.description = check.opt_str_param(description, 'description')
        self.is_optional = check.bool_param(is_optional, 'is_optional')
        self._default_value = default_value

    @property
    def default_provided(self):
        '''Was a default value provided

        Returns:
            bool: Yes or no
        '''
        return self._default_value != FIELD_NO_DEFAULT_PROVIDED

    @property
    def default_value(self):
        check.invariant(self.default_provided)

        if callable(self._default_value):
            return self._default_value()

        return self._default_value


class FieldDefinitionDictionary(dict):
    def __init__(self, ddict):
        check.dict_param(ddict, 'ddict', key_type=str, value_type=Field)
        super(FieldDefinitionDictionary, self).__init__(ddict)

    def __setitem__(self, _key, _value):
        check.failed('This dictionary is readonly')


class DagsterCompositeType(DagsterType):
    '''Dagster type representing a type with a list of named :py:class:`Field` objects.
    '''

    def __init__(self, name, fields, description=None):
        self.field_dict = FieldDefinitionDictionary(fields)
        super(DagsterCompositeType, self).__init__(name, description)

    def evaluate_value(self, _value):
        check.not_implemented('Must override')

    def iterate_types(self):
        for field_type in self.field_dict.values():
            for inner_type in field_type.dagster_type.iterate_types():
                yield inner_type
        yield self


class ConfigDictionary(DagsterCompositeType):
    '''Configuration dictionary.

    Typed-checked but then passed to implementations as a python dict

    Arguments:
      fields (dict): dictonary of :py:class:`Field` objects keyed by name'''

    def __init__(self, name, fields):
        super(ConfigDictionary, self).__init__(
            name,
            fields,
            'A configuration dictionary with typed fields',
        )

    def evaluate_value(self, value):
        if value is not None and not isinstance(value, dict):
            raise DagsterEvaluateValueError('Incoming value for composite must be dict')
        return process_incoming_composite_value(self, value, lambda val: val)


def process_incoming_composite_value(dagster_composite_type, incoming_value, ctor):
    check.inst_param(dagster_composite_type, 'dagster_composite_type', DagsterCompositeType)

    if incoming_value and not isinstance(incoming_value, dict):
        raise DagsterEvaluateValueError(
            'Value for composite type {type_name} must be a dict got {value}'.format(
                type_name=dagster_composite_type.name,
                value=incoming_value,
            )
        )

    incoming_value = check.opt_dict_param(incoming_value, 'incoming_value', key_type=str)
    check.callable_param(ctor, 'ctor')

    field_dict = dagster_composite_type.field_dict

    defined_args = set(field_dict.keys())
    received_args = set(incoming_value.keys())

    for received_arg in received_args:
        if received_arg not in defined_args:
            raise DagsterEvaluateValueError(
                'Field {received} not found. Defined fields: {defined}'.format(
                    defined=repr(defined_args),
                    received=received_arg,
                )
            )

    for expected_field, field_def in field_dict.items():
        if field_def.is_optional:
            continue

        check.invariant(not field_def.default_provided)

        if expected_field not in received_args:
            raise DagsterEvaluateValueError(
                'Did not not find {expected} on {type_name}. Defined fields: {defined}'.format(
                    expected=expected_field,
                    type_name=dagster_composite_type.name,
                    defined=repr(defined_args),
                )
            )

    fields_to_pass = {}

    for expected_field, field_def in field_dict.items():
        if expected_field in received_args:
            evaluation_result = field_def.dagster_type.evaluate_value(
                incoming_value[expected_field]
            )
            fields_to_pass[expected_field] = evaluation_result
        elif field_def.default_provided:
            fields_to_pass[expected_field] = field_def.default_value
        else:
            check.invariant(field_def.is_optional and not field_def.default_provided)

    return ctor(fields_to_pass)


String = DagsterStringType(name='String', description='A string.')
Path = DagsterStringType(
    name='Path',
    description='''
A string the represents a path. It is very useful for some tooling
to know that a string indeed represents a file path. That way they
can, for example, make the paths relative to a different location
for a particular execution environment.
''',
)
Int = _DagsterIntType()
Bool = _DagsterBoolType()
Any = _DagsterAnyType()
Dict = PythonObjectType('Dict', dict)
