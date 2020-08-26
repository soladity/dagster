from enum import Enum as PythonEnum

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class ConfigTypeKind(PythonEnum):
    ANY = "ANY"
    SCALAR = "SCALAR"
    ENUM = "ENUM"

    SELECTOR = "SELECTOR"
    STRICT_SHAPE = "STRICT_SHAPE"
    PERMISSIVE_SHAPE = "PERMISSIVE_SHAPE"
    SCALAR_UNION = "SCALAR_UNION"

    @staticmethod
    def has_fields(kind):
        check.inst_param(kind, "kind", ConfigTypeKind)
        return kind == ConfigTypeKind.SELECTOR or ConfigTypeKind.is_shape(kind)

    # Closed generic types
    ARRAY = "ARRAY"
    NONEABLE = "NONEABLE"

    @staticmethod
    def is_closed_generic(kind):
        check.inst_param(kind, "kind", ConfigTypeKind)
        return (
            kind == ConfigTypeKind.ARRAY
            or kind == ConfigTypeKind.NONEABLE
            or kind == ConfigTypeKind.SCALAR_UNION
        )

    @staticmethod
    def is_shape(kind):
        check.inst_param(kind, "kind", ConfigTypeKind)
        return kind == ConfigTypeKind.STRICT_SHAPE or kind == ConfigTypeKind.PERMISSIVE_SHAPE

    @staticmethod
    def is_selector(kind):
        check.inst_param(kind, "kind", ConfigTypeKind)
        return kind == ConfigTypeKind.SELECTOR


class ConfigType(object):
    """
    The class backing DagsterTypes as they are used processing configuration data.
    """

    def __init__(
        self, key, kind, given_name=None, description=None, type_params=None,
    ):

        self.key = check.str_param(key, "key")
        self.kind = check.inst_param(kind, "kind", ConfigTypeKind)
        self.given_name = check.opt_str_param(given_name, "given_name")
        self._description = check.opt_str_param(description, "description")
        self.type_params = (
            check.list_param(type_params, "type_params", of_type=ConfigType)
            if type_params
            else None
        )

    @property
    def description(self):
        return self._description

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.invariant(BuiltinEnum.contains(builtin_enum), "param must be member of BuiltinEnum")
        return _CONFIG_MAP[builtin_enum]

    def post_process(self, value):
        """
        Implement this in order to take a value provided by the user
        and perform computation on it. This can be done to coerce data types,
        fetch things from the environment (e.g. environment variables), or
        to do custom validation. If the value is not valid, throw a
        PostProcessingError. Otherwise return the coerced value.
        """
        return value


@whitelist_for_serdes
class ConfigScalarKind(PythonEnum):
    INT = "INT"
    STRING = "STRING"
    FLOAT = "FLOAT"
    BOOL = "BOOL"


# Scalars, Composites, Selectors, Lists, Optional, Any


class ConfigScalar(ConfigType):
    def __init__(self, key, given_name, scalar_kind, **kwargs):
        self.scalar_kind = check.inst_param(scalar_kind, "scalar_kind", ConfigScalarKind)
        super(ConfigScalar, self).__init__(
            key, given_name=given_name, kind=ConfigTypeKind.SCALAR, **kwargs
        )


class BuiltinConfigScalar(ConfigScalar):
    def __init__(self, scalar_kind, description=None):
        super(BuiltinConfigScalar, self).__init__(
            key=type(self).__name__,
            given_name=type(self).__name__,
            scalar_kind=scalar_kind,
            description=description,
        )


class Int(BuiltinConfigScalar):
    def __init__(self):
        super(Int, self).__init__(scalar_kind=ConfigScalarKind.INT, description="")


class String(BuiltinConfigScalar):
    def __init__(self):
        super(String, self).__init__(scalar_kind=ConfigScalarKind.STRING, description="")


class Bool(BuiltinConfigScalar):
    def __init__(self):
        super(Bool, self).__init__(scalar_kind=ConfigScalarKind.BOOL, description="")


class Float(BuiltinConfigScalar):
    def __init__(self):
        super(Float, self).__init__(scalar_kind=ConfigScalarKind.FLOAT, description="")

    def post_process(self, value):
        return float(value)


class Any(ConfigType):
    def __init__(self):
        super(Any, self).__init__(
            key="Any", given_name="Any", kind=ConfigTypeKind.ANY,
        )


class Noneable(ConfigType):
    def __init__(self, inner_type):
        from .field import resolve_to_config_type

        self.inner_type = resolve_to_config_type(inner_type)
        super(Noneable, self).__init__(
            key="Noneable.{inner_type}".format(inner_type=self.inner_type.key),
            kind=ConfigTypeKind.NONEABLE,
            type_params=[self.inner_type],
        )


class Array(ConfigType):
    def __init__(self, inner_type):
        from .field import resolve_to_config_type

        self.inner_type = resolve_to_config_type(inner_type)
        super(Array, self).__init__(
            key="Array.{inner_type}".format(inner_type=self.inner_type.key),
            type_params=[self.inner_type],
            kind=ConfigTypeKind.ARRAY,
        )

    @property
    def description(self):
        return "List of {inner_type}".format(inner_type=self.key)


class EnumValue(object):
    """Define an entry in a :py:func:`Enum`.

    Args:
        config_value (str):
            The string representation of the config to accept when passed.
        python_value (Optional[Any]):
            The python value to convert the enum entry in to. Defaults to the ``config_value``.
        description (Optional[str])

    """

    def __init__(self, config_value, python_value=None, description=None):
        self.config_value = check.str_param(config_value, "config_value")
        self.python_value = config_value if python_value is None else python_value
        self.description = check.opt_str_param(description, "description")


class Enum(ConfigType):
    """
    Defines a enum configuration type that allows one of a defined set of possible values.

    Args:
        name (str):
        enum_values (List[EnumValue]):

    Example:
        .. code-block:: python

            @solid(
                config_schema=Field(
                    Enum(
                        'CowboyType',
                        [
                            EnumValue('good'),
                            EnumValue('bad'),
                            EnumValue('ugly'),
                        ]
                    )
                )
            )
            def resolve_standoff(context):
                # ...
    """

    def __init__(self, name, enum_values):
        check.str_param(name, "name")
        super(Enum, self).__init__(key=name, given_name=name, kind=ConfigTypeKind.ENUM)
        self.enum_values = check.list_param(enum_values, "enum_values", of_type=EnumValue)
        self._valid_python_values = {ev.python_value for ev in enum_values}
        check.invariant(len(self._valid_python_values) == len(enum_values))
        self._valid_config_values = {ev.config_value for ev in enum_values}
        check.invariant(len(self._valid_config_values) == len(enum_values))

    @property
    def config_values(self):
        return [ev.config_value for ev in self.enum_values]

    def is_valid_config_enum_value(self, config_value):
        return config_value in self._valid_config_values

    def post_process(self, value):
        if isinstance(value, PythonEnum):
            value = value.name

        for ev in self.enum_values:
            if ev.config_value == value:
                return ev.python_value

        check.failed(
            (
                "Should never reach this. config_value should be pre-validated. "
                "Got {config_value}"
            ).format(config_value=value)
        )

    @classmethod
    def from_python_enum(cls, enum, name=None):
        """
        Create a Dagster enum corresponding to an existing Python enum.

        Args:
            enum (enum.EnumMeta):
                The class representing the enum.
            name (Optional[str]):
                The name for the enum. If not present, `enum.__name__` will be used.

        Example:
            .. code-block:: python
                class Color(enum.Enum):
                    RED = enum.auto()
                    GREEN = enum.auto()
                    BLUE = enum.auto()

                @solid(
                    config_schema={"color": Field(Enum.from_python_enum(Color))}
                )
                def select_color(context):
                    # ...
        """
        if name is None:
            name = enum.__name__
        return cls(name, [EnumValue(v.name, python_value=v) for v in enum])


class ScalarUnion(ConfigType):
    def __init__(
        self, scalar_type, non_scalar_schema, _key=None,
    ):
        from .field import resolve_to_config_type

        self.scalar_type = resolve_to_config_type(scalar_type)
        self.non_scalar_type = resolve_to_config_type(non_scalar_schema)

        check.param_invariant(self.scalar_type.kind == ConfigTypeKind.SCALAR, "scalar_type")
        check.param_invariant(
            self.non_scalar_type.kind
            in {ConfigTypeKind.STRICT_SHAPE, ConfigTypeKind.SELECTOR, ConfigTypeKind.ARRAY},
            "non_scalar_type",
        )

        # https://github.com/dagster-io/dagster/issues/2133
        key = check.opt_str_param(
            _key, "_key", "ScalarUnion.{}-{}".format(self.scalar_type.key, self.non_scalar_type.key)
        )

        super(ScalarUnion, self).__init__(
            key=key,
            kind=ConfigTypeKind.SCALAR_UNION,
            type_params=[self.scalar_type, self.non_scalar_type],
        )


ConfigAnyInstance = Any()
ConfigBoolInstance = Bool()
ConfigFloatInstance = Float()
ConfigIntInstance = Int()
ConfigStringInstance = String()
_CONFIG_MAP = {
    BuiltinEnum.ANY: ConfigAnyInstance,
    BuiltinEnum.BOOL: ConfigBoolInstance,
    BuiltinEnum.FLOAT: ConfigFloatInstance,
    BuiltinEnum.INT: ConfigIntInstance,
    BuiltinEnum.STRING: ConfigStringInstance,
}


_CONFIG_MAP_BY_NAME = {
    "Any": ConfigAnyInstance,
    "Bool": ConfigBoolInstance,
    "Float": ConfigFloatInstance,
    "Int": ConfigIntInstance,
    "String": ConfigStringInstance,
}

ALL_CONFIG_BUILTINS = set(_CONFIG_MAP.values())


def get_builtin_scalar_by_name(type_name):
    if type_name not in _CONFIG_MAP_BY_NAME:
        check.failed("Scalar {} is not supported".format(type_name))
    return _CONFIG_MAP_BY_NAME[type_name]
