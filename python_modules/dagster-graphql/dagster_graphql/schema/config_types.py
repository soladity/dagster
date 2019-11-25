from dagster_graphql import dauphin

from dagster import check
from dagster.core.meta.config_types import (
    ConfigTypeMeta,
    NonGenericTypeRefMeta,
    TypeRef,
    meta_from_config_type,
)
from dagster.core.types.config import ConfigType, ConfigTypeKind
from dagster.core.types.field import Field


class ConfigTypeSchema:
    @staticmethod
    def from_environment_schema(environment_schema):
        return ConfigTypeSchema(
            environment_schema.environment_type.key,
            list(map(meta_from_config_type, environment_schema.all_config_types())),
        )

    def __init__(self, root_type_key, config_type_metas):
        check.str_param(root_type_key, 'root_type_key')
        check.list_param(config_type_metas, 'config_type_meta', of_type=ConfigTypeMeta)

        self.config_type_metas = config_type_metas
        self.config_type_meta_by_key = {
            config_type_meta.key: config_type_meta for config_type_meta in config_type_metas
        }
        self.config_type_meta_by_name = {
            config_type_meta.name: config_type_meta
            for config_type_meta in config_type_metas
            if config_type_meta.name
        }
        self.root_type_meta = self.config_type_meta_by_key[root_type_key]

    def has_config_type(self, name):
        return name in self.config_type_meta_by_name

    def meta_from_type_ref(self, type_ref):
        check.inst_param(type_ref, 'type_ref', TypeRef)
        if isinstance(type_ref, NonGenericTypeRefMeta):
            return self.config_type_meta_by_key[type_ref.key]
        elif isinstance(type_ref, ConfigTypeMeta):
            return type_ref
        else:
            check.failed('should not reach')


def to_dauphin_config_type_field(name, field):
    check.str_param(name, 'name')
    check.inst_param(field, 'field', Field)
    return DauphinConfigTypeField(
        config_type=to_dauphin_config_type(field.config_type),
        name=name,
        description=field.description,
        default_value=field.default_value_as_str if field.default_provided else None,
        is_optional=field.is_optional,
    )


def to_dauphin_config_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    # all types inherit from the DauphinConfigType interface
    # which require the same set of fields. Passing them
    # as kwargs into each derived type.
    type_kwargs = _dauphin_config_type_kwargs_args_from_type(config_type)
    if config_type.kind == ConfigTypeKind.ENUM:
        return DauphinEnumConfigType(
            values=[
                DauphinEnumConfigValue(value=ev.config_value, description=ev.description)
                for ev in config_type.enum_values
            ],
            **type_kwargs
        )
    elif ConfigTypeKind.has_fields(config_type.kind):
        return DauphinCompositeConfigType(
            fields=sorted(
                [
                    to_dauphin_config_type_field(name, field)
                    for name, field in config_type.fields.items()
                ],
                key=lambda field: field.name,
            ),
            inner_types=_resolve_inner_types(config_type),
            **type_kwargs
        )
    elif config_type.kind == ConfigTypeKind.LIST:
        return DauphinListConfigType(
            of_type=to_dauphin_config_type(config_type.inner_type),
            inner_types=_resolve_inner_types(config_type),
            **type_kwargs
        )
    elif config_type.kind == ConfigTypeKind.NULLABLE:
        return DauphinNullableConfigType(
            of_type=to_dauphin_config_type(config_type.inner_type),
            inner_types=_resolve_inner_types(config_type),
            **type_kwargs
        )
    elif config_type.kind == ConfigTypeKind.SCALAR or config_type.kind == ConfigTypeKind.REGULAR:
        return DauphinRegularConfigType(**type_kwargs)
    else:
        # Set and Tuple unsupported in the graphql layer
        # https://github.com/dagster-io/dagster/issues/1925
        check.not_implemented(
            'Unsupported kind {kind} in config_type {key}'.format(
                kind=config_type.kind, key=config_type.key
            )
        )


def to_dauphin_config_type_from_meta(config_type_schema, config_type_meta):
    check.inst_param(config_type_meta, 'config_type_meta', ConfigTypeMeta)

    type_kwargs = _dauphin_config_type_kwargs_args_from_meta(config_type_meta)

    if config_type_meta.kind == ConfigTypeKind.ENUM:
        return DauphinEnumConfigType(
            values=[
                DauphinEnumConfigValue(value=ev.value, description=ev.description)
                for ev in config_type_meta.enum_values
            ],
            **type_kwargs
        )
    elif ConfigTypeKind.has_fields(config_type_meta.kind):
        return DauphinCompositeConfigType(
            fields=sorted(
                [
                    DauphinConfigTypeField(
                        config_type=to_dauphin_config_type_from_meta(
                            config_type_schema,
                            config_type_schema.meta_from_type_ref(field_meta.type_ref),
                        ),
                        name=field_meta.name,
                        description=field_meta.description,
                        default_value=field_meta.default_value_as_str
                        if field_meta.default_provided
                        else None,
                        is_optional=field_meta.is_optional,
                    )
                    for field_meta in config_type_meta.fields
                ],
                key=lambda field: field.name,
            ),
            inner_types=_resolve_inner_types_for_meta(config_type_schema, config_type_meta),
            **type_kwargs
        )

    elif config_type_meta.kind == ConfigTypeKind.LIST:
        return DauphinListConfigType(
            of_type=to_dauphin_config_type_from_meta(
                config_type_schema,
                config_type_schema.meta_from_type_ref(config_type_meta.type_param_refs[0]),
            ),
            inner_types=_resolve_inner_types_for_meta(config_type_schema, config_type_meta),
            **type_kwargs
        )
    elif config_type_meta.kind == ConfigTypeKind.NULLABLE:
        return DauphinNullableConfigType(
            of_type=to_dauphin_config_type_from_meta(
                config_type_schema,
                config_type_schema.meta_from_type_ref(config_type_meta.type_param_refs[0]),
            ),
            inner_types=_resolve_inner_types_for_meta(config_type_schema, config_type_meta),
            **type_kwargs
        )
    elif (
        config_type_meta.kind == ConfigTypeKind.REGULAR
        or config_type_meta.kind == ConfigTypeKind.SCALAR
    ):
        return DauphinRegularConfigType(**type_kwargs)
    # this will break for sets and tuples
    # http://github.com/dagster-io/dagster/issues/1925
    else:
        raise NotImplementedError()


def _yield_inner_types_for_meta(config_type_schema, config_type_meta):
    if config_type_meta.inner_type_refs:
        for inner_type_ref in config_type_meta.inner_type_refs:
            inner_type_meta = config_type_schema.meta_from_type_ref(inner_type_ref)

            yield inner_type_meta
            for recursed_type_meta in _yield_inner_types_for_meta(
                config_type_schema, inner_type_meta
            ):
                yield recursed_type_meta


def _resolve_inner_types_for_meta(config_type_schema, config_type_meta):
    '''
    Recurse through all the types down to the leaf types from a given type
    root and dedup them.
    '''
    return list(
        {
            type_meta.key: to_dauphin_config_type_from_meta(config_type_schema, type_meta)
            for type_meta in _yield_inner_types_for_meta(config_type_schema, config_type_meta)
        }.values()
    )


def _dauphin_config_type_kwargs_args_from_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    return dict(
        key=config_type.key,
        name=config_type.name,
        description=config_type.description,
        is_builtin=config_type.type_attributes.is_builtin,
        is_list=config_type.is_list,
        is_nullable=config_type.is_nullable,
        is_selector=config_type.is_selector,
        is_system_generated=config_type.type_attributes.is_system_config,
    )


def _dauphin_config_type_kwargs_args_from_meta(config_type_meta):
    check.inst_param(config_type_meta, 'config_type_meta', ConfigTypeMeta)
    return dict(
        key=config_type_meta.key,
        name=config_type_meta.name,
        description=config_type_meta.description,
        is_builtin=config_type_meta.is_builtin,
        is_list=config_type_meta.kind == ConfigTypeKind.LIST,
        is_nullable=config_type_meta.kind == ConfigTypeKind.NULLABLE,
        is_selector=config_type_meta.kind == ConfigTypeKind.SELECTOR,
        is_system_generated=config_type_meta.is_system_config,
    )


class DauphinConfigType(dauphin.Interface):
    class Meta:
        name = 'ConfigType'

    key = dauphin.NonNull(dauphin.String)
    name = dauphin.String()
    description = dauphin.String()

    inner_types = dauphin.non_null_list('ConfigType')

    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_selector = dauphin.NonNull(dauphin.Boolean)

    is_builtin = dauphin.NonNull(
        dauphin.Boolean,
        description='''
True if the system defines it and it is the same type across pipelines.
Examples include "Int" and "String."''',
    )

    is_system_generated = dauphin.NonNull(
        dauphin.Boolean,
        description='''
Dagster generates types for base elements of the config system (e.g. the solids and
context field of the base environment). These types are always present
and are typically not relevant to an end user. This flag allows tool authors to
filter out those types by default.
''',
    )


def _resolve_inner_types(config_type):
    return list(map(to_dauphin_config_type, config_type.inner_types))


class DauphinRegularConfigType(dauphin.ObjectType):
    def __init__(self, **kwargs):
        super(DauphinRegularConfigType, self).__init__(inner_types=[], **kwargs)

    class Meta:
        name = 'RegularConfigType'
        interfaces = [DauphinConfigType]


class DauphinWrappingConfigType(dauphin.Interface):
    class Meta:
        name = 'WrappingConfigType'

    of_type = dauphin.Field(dauphin.NonNull(DauphinConfigType))


class DauphinListConfigType(dauphin.ObjectType):
    def __init__(self, of_type, inner_types, **kwargs):
        super(DauphinListConfigType, self).__init__(
            of_type=check.inst_param(of_type, 'of_type', dauphin.ObjectType),
            inner_types=check.list_param(inner_types, 'inner_types', of_type=dauphin.ObjectType),
            **kwargs
        )

    class Meta:
        name = 'ListConfigType'
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]


class DauphinNullableConfigType(dauphin.ObjectType):
    def __init__(self, of_type, inner_types, **kwargs):
        super(DauphinNullableConfigType, self).__init__(
            of_type=check.inst_param(of_type, 'of_type', dauphin.ObjectType),
            inner_types=check.list_param(inner_types, 'inner_types', of_type=dauphin.ObjectType),
            **kwargs
        )

    class Meta:
        name = 'NullableConfigType'
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]


class DauphinEnumConfigType(dauphin.ObjectType):
    def __init__(self, values, **kwargs):
        super(DauphinEnumConfigType, self).__init__(
            values=check.list_param(values, 'values', of_type=DauphinEnumConfigValue), **kwargs
        )

    class Meta:
        name = 'EnumConfigType'
        interfaces = [DauphinConfigType]

    values = dauphin.non_null_list('EnumConfigValue')


class DauphinEnumConfigValue(dauphin.ObjectType):
    class Meta:
        name = 'EnumConfigValue'

    value = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinCompositeConfigType(dauphin.ObjectType):
    def __init__(self, fields, inner_types, **kwargs):
        super(DauphinCompositeConfigType, self).__init__(
            fields=check.list_param(fields, 'fields', of_type=DauphinConfigTypeField),
            inner_types=check.opt_list_param(
                inner_types, 'inner_types', of_type=dauphin.ObjectType
            ),
            **kwargs
        )

    class Meta:
        name = 'CompositeConfigType'
        interfaces = [DauphinConfigType]

    fields = dauphin.non_null_list('ConfigTypeField')


class DauphinConfigTypeField(dauphin.ObjectType):
    class Meta:
        name = 'ConfigTypeField'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config_type = dauphin.NonNull('ConfigType')
    default_value = dauphin.String()
    is_optional = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, config_type, name, description, default_value, is_optional):
        super(DauphinConfigTypeField, self).__init__(
            config_type=check.inst_param(config_type, 'config_type', dauphin.ObjectType),
            name=name,
            description=description,
            default_value=default_value,
            is_optional=is_optional,
        )
