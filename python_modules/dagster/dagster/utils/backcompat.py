import warnings

from dagster import check


def canonicalize_backcompat_args(new_val, new_arg, old_val, old_arg, coerce_old_to_new=None):
    '''
    Utility for managing backwards compatibility of two related arguments.

    For example if you had an existing function

    def is_new(old_flag):
        return not new_flag

    And you decided you wanted a new function to be:

    def is_new(new_flag):
        return new_flag

    However you want an in between period where either flag is accepted. Use
    canonicalize_backcompat_args to manage that:

    def is_new(old_flag=None, new_flag=None):
        return canonicalize_backcompat_args(
            new_val=new_flag,
            new_arg='new_flag',
            old_val=old_flag,
            old_arg='old_flag',
            coerce_old_to_new=lambda val: not val,
        )


    In this example, if the caller sets both new_flag and old_flag, it will fail by throwing
    a CheckError. If the caller sets old_flag, it will run it through the coercion function
    , warn, and then execute.

    canonicalize_backcompat_args returns the value as if *only* new_val were specified
    '''
    check.str_param(new_arg, 'new_arg')
    check.str_param(old_arg, 'old_arg')
    check.opt_callable_param(coerce_old_to_new, 'coerce_old_to_new')
    if new_val is not None:
        if old_val is not None:
            check.failed(
                'Do not use deprecated "{old_arg}" now that you are using "{new_arg}".'.format(
                    old_arg=old_arg, new_arg=new_arg
                )
            )
        return new_val
    if old_val is not None:
        warnings.warn(
            '"{old_arg}" is deprecated, use "{new_arg}" instead.'.format(
                old_arg=old_arg, new_arg=new_arg
            ),
            # This punches up to the caller of canonicalize_backcompat_args
            stacklevel=3,
        )
        return coerce_old_to_new(old_val) if coerce_old_to_new else old_val

    return new_val
