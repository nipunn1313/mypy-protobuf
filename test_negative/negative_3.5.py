"""
This code is intended to have mypy failures which we will ensure
show up in the output.
"""

import typing

import grpc

from testproto.grpc.dummy_pb2_grpc import (
    DummyRequest,
    DummyReply,
    DummyServiceServicer,
    DummyServiceStub,
)

stub0 = DummyServiceStub()  # E:3.5
channel = grpc.insecure_channel("127.0.0.1:8080")
stub1 = DummyServiceStub(channel)
request1 = DummyRequest()

response1 = stub1.UnaryUnary(request1)
value = response1.value
value2 = response1.not_exists  # E:3.5
for result1 in stub1.UnaryUnary(request1):  # E:3.5
    pass

for result2 in stub1.UnaryStream(request1):
    value = result2.value
    value2 = result2.not_exists  # E:3.5
response2 = stub1.UnaryStream(request1)
value = response2.value  # E:3.5


def iter_requests() -> typing.Generator[DummyRequest, None, None]:
    yield request1


response3 = stub1.StreamUnary(request1)  # E:3.5
response4 = stub1.StreamUnary(iter_requests())
for result3 in stub1.StreamUnary(request1):  # E:3.5
    pass

for result4 in stub1.StreamStream(request1):  # E:3.5
    pass
for result5 in stub1.StreamStream(iter_requests()):
    value = result5.value
    value2 = result5.not_exists  # E:3.5


class GoodServicer(DummyServiceServicer):
    def UnaryUnary(
            self,
            request: DummyRequest,
            context: grpc.ServicerContext,
    ) -> DummyReply:
        return DummyReply()

    def UnaryStream(
            self,
            request: DummyRequest,
            context: grpc.ServicerContext,
    ) -> typing.Iterator[DummyReply]:
        yield DummyReply()

    def StreamUnary(
            self,
            request: typing.Iterator[DummyRequest],
            context: grpc.ServicerContext,
    ) -> DummyReply:
        for data in request:
            pass
        return DummyReply()

    def StreamStream(
            self,
            request: typing.Iterator[DummyRequest],
            context: grpc.ServicerContext,
    ) -> typing.Iterator[DummyReply]:
        for data in request:
            yield DummyReply()


class BadServicer(DummyServiceServicer):
    def UnaryUnary(  # E:3.5
            self,
            request: typing.Iterator[DummyRequest],
            context: grpc.ServicerContext,
    ) -> typing.Iterator[DummyReply]:
        for data in request:
            yield DummyReply()

    def UnaryStream(  # E:3.5
            self,
            request: typing.Iterator[DummyRequest],
            context: grpc.ServicerContext,
    ) -> DummyReply:
        for data in request:
            pass
        return DummyReply()

    def StreamUnary(  # E:3.5
            self,
            request: DummyRequest,
            context: grpc.ServicerContext,
    ) -> typing.Iterator[DummyReply]:
        yield DummyReply()
