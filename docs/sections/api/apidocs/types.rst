Types
=========

.. module:: dagster

Dagster includes facilities for typing the input and output values of solids ("runtime" types), as
well as for writing strongly typed config schemas to support tools like Dagit's config editor
("config" types).

Built-in types
--------------

.. attribute:: Any

    Use this type for any input, output, or config field whose type is unconstrained
    
    All values are considered to be instances of ``Any``. 

    **Examples:**

    .. code-block:: python

        @solid
        def identity(_, x: Any) -> Any:
            return x

        # Untyped inputs and outputs are implicitly typed Any
        @solid
        def identity_imp(_, x):
            return x

        # Explicitly typed on Python 2
        @solid(
            input_defs=[InputDefinition('x', dagster_type=Any)],
            output_defs=[OutputDefinition(dagster_type=Any)]
        )
        def identity_py2(_, x):
            return x

        @solid(config_field=Field(Any))
        def any_config(context):
            return context.solid_config


.. attribute:: Bool

    Use this type for any boolean input, output, or config_field. At runtime, this will perform an
    ``isinstance(value, bool)`` check. You may also use the ordinary :py:class:`~python:bool`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def boolean(_, x: Bool) -> String:
            return 'true' if x else 'false'

        @solid
        def empty_string(_, x: String) -> bool:
            return len(x) == 0

        # Python 2
        @solid(
            input_defs=[InputDefinition('x', dagster_type=Bool)],
            output_defs=[OutputDefinition(dagster_type=String)]
        )
        def boolean_py2(_, x):
            return 'true' if x else 'false'

        @solid(
            input_defs=[InputDefinition('x', dagster_type=String)],
            output_defs=[OutputDefinition(dagster_type=bool)]
        )
        def empty_string_py2(_, x):
            return len(x) == 0

        @solid(config_field=Field(Bool))
        def bool_config(context):
            return 'true' if context.solid_config else 'false'


.. attribute:: Int

    Use this type for any integer input or output. At runtime, this will perform an
    ``isinstance(value, six.integer_types)`` check -- that is, on Python 2, both ``long`` and
    ``int`` will pass this check. In Python 3, you may also use the ordinary :py:class:`~python:int`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def add_3(_, x: Int) -> int:
            return x + 3

        # Python 2
        @solid(
            input_defs=[InputDefinition('x', dagster_type=Int)],
            output_defs=[OutputDefinition(dagster_type=int)]
        )
        def add_3_py2(_, x):
            return x + 3


.. attribute:: Float

    Use this type for any float input, output, or config value. At runtime, this will perform an
    ``isinstance(value, float)`` check. You may also use the ordinary :py:class:`~python:float`
    type as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def div_2(_, x: Float) -> float:
            return x / 2

        @solid(
            input_defs=[InputDefinition('x', dagster_type=Float)],
            output_defs=[OutputDefinition(dagster_type=float)]
        )
        def div_2_py_2(_, x):
            return x / 2

        @solid(config_field=Field(Float))
        def div_y(context, x: Float) -> float:
            return x / context.solid_config


.. attribute:: String

    Use this type for any string input, output, or config value. At runtime, this will perform an
    ``isinstance(value, six.string_types)`` -- that is on Python 2, both ``unicode`` and ``str``
    will pass this check. In Python 3, you may also use the ordinary :py:class:`~python:str` type
    as an alias.

    **Examples:**

    .. code-block:: python

        @solid
        def concat(_, x: String, y: str) -> str:
            return x + y

        @solid(
            input_defs=[
                InputDefinition('x', dagster_type=String),
                InputDefinition('y', dagster_type=str)
            ],
            output_defs=[OutputDefinition(dagster_type=str)]
        )
        def concat_py_2(_, x, y):
            return x + y

        @solid(config_field=Field(String))
        def hello(context) -> str:
            return 'Hello, {friend}!'.format(friend=context.solid_config)


.. attribute:: Path

    Use this type to indicate that a string input, output, or config value represents a path. At
    runtime, this will perform an ``isinstance(value, six.string_types)`` -- that is on Python 2,
    both ``unicode`` and ``str`` will pass this check. 

    **Examples:**

    .. code-block:: python

        @solid
        def exists(_, path: Path) -> Bool:
            return os.path.exists(path)


        @solid(
            input_defs=[InputDefinition('path', dagster_type=Path)],
            output_defs=[OutputDefinition(dagster_type=Bool)]
        )
        def exists_py2(_, path):
            return os.path.exists(path)

        @solid(config_field=Field(Path))
        def unpickle(context) -> Any:
            with open(context.solid_config, 'rb') as fd:
                return pickle.load(fd)


.. attribute:: Nothing

    Use this type only for inputs and outputs, in order to establish an execution dependency without
    communicating a value. Inputs of this type will not be pased to the solid compute function, so
    it is necessary to use the explicit :py:class:`InputDefinition` API to define them rather than
    the Python 3 type hint syntax.

    All values are considered to be instances of ``Nothing``. 

    **Examples:**

    .. code-block:: python

        @solid
        def wait(_) -> Nothing:
            time.sleep(1)
            return
        
        @solid(
            InputDefinition('ready', dagster_type=Nothing)
        )
        def done(_) -> str:
            return 'done'

        @pipeline
        def nothing_pipeline():
            done(wait())

        # Any value will pass the type check for Nothing
        @solid
        def wait_int(_) -> Int:
            time.sleep(1)
            return 1

        @pipeline
        def nothing_int_pipeline():
            done(wait_int())


.. attribute:: Optional

    Use this type only for inputs and outputs, if the value can also be ``None``. For config values,
    set the ``is_optional`` parameter on :py:func:`Field <Field>`.

    **Examples:**

    .. code-block:: python

        @solid
        def nullable_concat(_, x: String, y: Optional[String]) -> String:
            return x + (y or '')

        # Python 2
        @solid(
            input_defs=[
                InputDefinition('x', dagster_type=String),
                InputDefinition('y', dagster_type=Optional[String])
            ],
            output_defs=[OutputDefinition(dagster_type=String)]
        )
        def nullable_concat_py2(_, x, y) -> String:
            return x + (y or '')

.. attribute:: List

    Use this type for inputs, outputs, or config values that are lists of values of the inner type.

    Lists are also the appropriate input types when fanning in multiple outputs using a
    :py:class:`MultiDependencyDefinition` or the equivalent composition function syntax.

    **Examples:**

    .. code-block:: python

        @solid
        def concat_list(_, xs: List[String]) -> String:
            return ''.join(xs)

        # Python 2
        @solid(
            input_defs=[InputDefinition('xs', dagster_type=List[String])],
            output_defs=[OutputDefinition(dagster_type=String)]
        )
        def concat_list_py2(_, xs) -> String:
            return ''.join(xs)

        @solid(config_field=Field(List[String]))
        def concat_config(context) -> String:
            return ''.join(context.solid_config)

        # Fanning in multiple outputs
        @solid
        def emit_1(_) -> int:
            return 1

        @solid
        def emit_2(_) -> int:
            return 2

        @solid
        def emit_3(_) -> int:
            return 3

        @solid
        def sum_solid(_, xs: List[int]) -> int:
            return sum(xs)

        @pipeline
        def sum_pipeline():
            sum_solid([emit_1(), emit_2(), emit_3()])


.. attribute:: Dict

    Use this type for inputs, outputs, or config values that are dicts.

    For inputs and outputs, you may optionally specify the key and value types using the square
    brackets syntax for Python typing.

    For config values, you should pass an argument that is itself a dict from string keys to
    :py:func:`Field <Field>` values, which will define the schema of the config dict. For config
    values where you do not intend to enforce a schema on the dict, use :py:class:`PermissiveDict`.
    (If the top level ``config_field`` of a solid is a dict, as is usually the case, you may also
    use the ``config`` param on :py:func:`@solid <solid>` and omit the top-level ``Dict`` type.)

    **Examples:**

    .. code-block:: python

        @solid
        def repeat(_, spec: Dict) -> str:
            return spec['word'] * spec['times']

        # Python 2
        @solid(
            input_defs=[InputDefinition('spec', dagster_type=Dict)],
            output_defs=[OutputDefinition(String)]
        )
        def repeat_py2(_, spec):
            return spec['word'] * spec['times']

        @solid(config_field=Field(Dict({'word': Field(String), 'times': Field(Int)})))
        def repeat_config(context) -> str:
            return context.solid_config['word'] * context.solid_config['times']


-----

Config Types
------------

The following types are used to describe the schema of configuration
data via ``config_field``. They are used in conjunction with the
builtin types above.

.. autofunction:: Field

.. autofunction:: Selector

.. autofunction:: PermissiveDict

-----

Making New Types
----------------

.. autofunction:: as_dagster_type

.. autofunction:: dagster_type

.. autofunction:: define_python_dagster_type

.. autoclass:: RuntimeType

.. autoclass:: ConfigType

.. autofunction:: NamedDict

.. autofunction:: input_hydration_config

.. autofunction:: output_materialization_config

.. autoclass:: ConfigScalar
