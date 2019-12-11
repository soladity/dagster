from __future__ import absolute_import

from dagster_graphql import dauphin


def create_schema():
    # dauphin depends on import-based side effects
    # pylint: disable=W0611
    from . import (
        config_types,
        errors,
        execution,
        paging,
        pipelines,
        roots,
        runs,
        schedules,
        runtime_types,
    )

    return dauphin.create_schema()
