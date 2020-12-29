import grpc
import typing
from concurrent import futures

from testproto.grpc import dummy_pb2, dummy_pb2_grpc

ADDRESS = "localhost:22222"


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
        request: typing.Iterator[dummy_pb2.DummyRequest],
        context: grpc.ServicerContext,
    ) -> dummy_pb2.DummyReply:
        return dummy_pb2.DummyReply(value="".join(data.value for data in request))

    def StreamStream(
        self,
        request: typing.Iterator[dummy_pb2.DummyRequest],
        context: grpc.ServicerContext,
    ) -> typing.Iterator[dummy_pb2.DummyReply]:
        for data in request:
            yield dummy_pb2.DummyReply(value=data.value.upper())


def make_server():
    # type: () -> grpc.Server

    server = grpc.server(futures.ThreadPoolExecutor())
    servicer = Servicer()
    server.add_insecure_port(ADDRESS)
    dummy_pb2_grpc.add_DummyServiceServicer_to_server(servicer, server)
    return server


def test_grpc():
    # type: () -> None

    server = make_server()
    server.start()
    channel = grpc.insecure_channel(ADDRESS)
    client = dummy_pb2_grpc.DummyServiceStub(channel)
    request = dummy_pb2.DummyRequest(value="cprg")
    result1 = client.UnaryUnary(request)
    result2 = client.UnaryStream(dummy_pb2.DummyRequest(value=result1.value))
    result2_list = list(result2)
    assert len(result2_list) == 4
    result3 = client.StreamStream(
        dummy_pb2.DummyRequest(value=part.value) for part in result2_list
    )
    result3_list = list(result3)
    assert len(result3_list) == 4
    result4 = client.StreamUnary(
        dummy_pb2.DummyRequest(value=part.value) for part in result3_list
    )
    assert result4.value == "GRPC"
    server.stop(None)
