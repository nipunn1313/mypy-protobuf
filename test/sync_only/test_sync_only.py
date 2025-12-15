"""
Type-checking and runtime test for sync_only GRPC stubs.

This module validates that stubs generated with the only_sync flag have the correct types:
- Regular (non-generic) Stub class that only accepts grpc.Channel
- Servicer methods use Iterator for client streaming (not _MaybeAsyncIterator)
- add_XXXServicer_to_server accepts grpc.Server
"""

from concurrent import futures

import grpc
import typing_extensions as typing
from testproto.grpc import dummy_pb2, dummy_pb2_grpc

ADDRESS = "localhost:22224"


class Servicer(dummy_pb2_grpc.DummyServiceServicer):
    def UnaryUnary(
        self,
        request: dummy_pb2.DummyRequest,
        context: grpc.ServicerContext,
    ) -> dummy_pb2.DummyReply:
        return dummy_pb2.DummyReply(value=request.value[::-1])

    def UnaryStream(
        self,
        request: dummy_pb2.DummyRequest,
        context: grpc.ServicerContext,
    ) -> typing.Iterator[dummy_pb2.DummyReply]:
        for char in request.value:
            yield dummy_pb2.DummyReply(value=char)

    def StreamUnary(
        self,
        request_iterator: typing.Iterator[dummy_pb2.DummyRequest],
        context: grpc.ServicerContext,
    ) -> dummy_pb2.DummyReply:
        return dummy_pb2.DummyReply(value="".join(data.value for data in request_iterator))

    def StreamStream(
        self,
        request_iterator: typing.Iterator[dummy_pb2.DummyRequest],
        context: grpc.ServicerContext,
    ) -> typing.Iterator[dummy_pb2.DummyReply]:
        for data in request_iterator:
            yield dummy_pb2.DummyReply(value=data.value.upper())


def make_server() -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor())
    servicer = Servicer()
    server.add_insecure_port(ADDRESS)
    dummy_pb2_grpc.add_DummyServiceServicer_to_server(servicer, server)
    return server


def test_sync_only_grpc() -> None:
    server = make_server()
    server.start()
    channel = grpc.insecure_channel(ADDRESS)
    client = dummy_pb2_grpc.DummyServiceStub(channel)
    request = dummy_pb2.DummyRequest(value="cprg")
    result1 = client.UnaryUnary(request)
    result2 = client.UnaryStream(dummy_pb2.DummyRequest(value=result1.value))
    result2_list = list(result2)
    assert len(result2_list) == 4
    result3 = client.StreamStream(dummy_pb2.DummyRequest(value=part.value) for part in result2_list)
    result3_list = list(result3)
    assert len(result3_list) == 4
    result4 = client.StreamUnary(dummy_pb2.DummyRequest(value=part.value) for part in result3_list)
    assert result4.value == "GRPC"

    # test future() in MultiCallable
    future_test: grpc._CallFuture[dummy_pb2.DummyReply] = client.UnaryUnary.future(request)
    result5 = future_test.result()
    assert result5.value == "grpc"

    # test params on __call__ in MultiCallable
    result6: dummy_pb2.DummyReply = client.UnaryUnary(request, timeout=4, metadata=(("test", "metadata"), ("cheems", "many")))
    assert result6.value == "grpc"

    server.stop(None)

    class TestAttribute:
        stub: dummy_pb2_grpc.DummyServiceStub

        def __init__(self) -> None:
            self.stub = dummy_pb2_grpc.DummyServiceStub(grpc.insecure_channel(ADDRESS))

        def test(self) -> None:
            val = self.stub.UnaryUnary(dummy_pb2.DummyRequest(value="test"))
            typing.assert_type(val, dummy_pb2.DummyReply)
