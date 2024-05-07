import typing

import grpc.aio
import pytest
from testproto.grpc import dummy_pb2, dummy_pb2_grpc

ADDRESS = "localhost:22223"


class Servicer(dummy_pb2_grpc.DummyServiceServicer):
    async def UnaryUnary(
        self,
        request: dummy_pb2.DummyRequest,
        context: grpc.aio.ServicerContext,
    ) -> dummy_pb2.DummyReply:
        return dummy_pb2.DummyReply(value=request.value[::-1])

    async def UnaryStream(
        self,
        request: dummy_pb2.DummyRequest,
        context: grpc.aio.ServicerContext,
    ) -> typing.AsyncIterator[dummy_pb2.DummyReply]:
        for char in request.value:
            yield dummy_pb2.DummyReply(value=char)

    async def StreamUnary(
        self,
        request_iterator: typing.AsyncIterator[dummy_pb2.DummyRequest],
        context: grpc.aio.ServicerContext,
    ) -> dummy_pb2.DummyReply:
        values = [data.value async for data in request_iterator]
        return dummy_pb2.DummyReply(value="".join(values))

    async def StreamStream(
        self,
        request_iterator: typing.AsyncIterator[dummy_pb2.DummyRequest],
        context: grpc.aio.ServicerContext,
    ) -> typing.AsyncIterator[dummy_pb2.DummyReply]:
        async for data in request_iterator:
            yield dummy_pb2.DummyReply(value=data.value.upper())


def make_server() -> grpc.aio.Server:
    server = grpc.aio.server()
    servicer = Servicer()
    server.add_insecure_port(ADDRESS)
    dummy_pb2_grpc.add_DummyServiceServicer_to_server(servicer, server)
    return server


@pytest.mark.asyncio
async def test_grpc() -> None:
    server = make_server()
    await server.start()
    async with grpc.aio.insecure_channel(ADDRESS) as channel:
        client = dummy_pb2_grpc.DummyServiceStub(channel)
        request = dummy_pb2.DummyRequest(value="cprg")
        result1 = await client.UnaryUnary(request)
        result2 = client.UnaryStream(dummy_pb2.DummyRequest(value=result1.value))
        result2_list = [r async for r in result2]
        assert len(result2_list) == 4
        result3 = client.StreamStream(dummy_pb2.DummyRequest(value=part.value) for part in result2_list)
        result3_list = [r async for r in result3]
        assert len(result3_list) == 4
        result4 = await client.StreamUnary(dummy_pb2.DummyRequest(value=part.value) for part in result3_list)
        assert result4.value == "GRPC"

    await server.stop(None)
