import time

import pytest
from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
    LocationStateSubscriber,
)

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite


class TestSubscribeToGrpcServerEvents(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.readonly_sqlite_instance_deployed_grpc_env()]
    )
):
    @pytest.mark.skip
    def test_grpc_server_handle_message_subscription(self, graphql_context):
        events = []
        test_subscriber = LocationStateSubscriber(events.append)
        handle = next(
            iter(
                graphql_context._workspace.repository_location_handles  # pylint: disable=protected-access
            )
        )
        handle.add_state_subscriber(test_subscriber)
        handle.client.shutdown_server()

        # Wait for event
        start_time = time.time()
        timeout = 30
        while not len(events) > 0:
            if time.time() - start_time > timeout:
                break
            time.sleep(1)

        assert len(events) == 1
        assert isinstance(events[0], LocationStateChangeEvent)
        assert events[0].event_type == LocationStateChangeEventType.LOCATION_ERROR
