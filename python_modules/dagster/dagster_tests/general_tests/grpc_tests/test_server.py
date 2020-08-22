import threading
import time

from dagster.grpc.client import ephemeral_grpc_api_client


def _stream_events_target(results, api_client):
    for result in api_client.streaming_ping(sequence_length=100000, echo="foo"):
        results.append(result)


def test_streaming_terminate():
    with ephemeral_grpc_api_client() as api_client:
        streaming_results = []
        stream_events_result_thread = threading.Thread(
            target=_stream_events_target, args=[streaming_results, api_client]
        )
        stream_events_result_thread.daemon = True
        stream_events_result_thread.start()
        while not streaming_results:
            time.sleep(0.001)
        res = api_client.shutdown_server()
        assert res.success
        assert res.serializable_error_info is None

        stream_events_result_thread.join()
        assert len(streaming_results) == 100000

        api_client._server_process.wait()  # pylint: disable=protected-access
        assert api_client._server_process.poll() == 0  # pylint: disable=protected-access
