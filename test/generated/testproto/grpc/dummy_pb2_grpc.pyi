"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
https://github.com/vmagamedov/grpclib/blob/master/tests/dummy.proto"""
import abc
import collections.abc
import grpc
import grpc.aio
import testproto.grpc.dummy_pb2
import typing

_T = typing.TypeVar('_T')

class _MaybeAsyncIterator(collections.abc.AsyncIterator[_T], collections.abc.Iterator[_T], metaclass=abc.ABCMeta):
    ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore[misc, type-arg]
    ...

class DummyServiceStub:
    """DummyService"""

    def __init__(self, channel: typing.Union[grpc.Channel, grpc.aio.Channel]) -> None: ...
    UnaryUnary: grpc.UnaryUnaryMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """UnaryUnary"""
    UnaryStream: grpc.UnaryStreamMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """UnaryStream"""
    StreamUnary: grpc.StreamUnaryMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """StreamUnary"""
    StreamStream: grpc.StreamStreamMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """StreamStream"""

class DummyServiceAsyncStub:
    """DummyService"""

    UnaryUnary: grpc.aio.UnaryUnaryMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """UnaryUnary"""
    UnaryStream: grpc.aio.UnaryStreamMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """UnaryStream"""
    StreamUnary: grpc.aio.StreamUnaryMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """StreamUnary"""
    StreamStream: grpc.aio.StreamStreamMultiCallable[
        testproto.grpc.dummy_pb2.DummyRequest,
        testproto.grpc.dummy_pb2.DummyReply,
    ]
    """StreamStream"""

class DummyServiceServicer(metaclass=abc.ABCMeta):
    """DummyService"""

    @abc.abstractmethod
    def UnaryUnary(
        self,
        request: testproto.grpc.dummy_pb2.DummyRequest,
        context: _ServicerContext,
    ) -> typing.Union[testproto.grpc.dummy_pb2.DummyReply, collections.abc.Awaitable[testproto.grpc.dummy_pb2.DummyReply]]:
        """UnaryUnary"""
    @abc.abstractmethod
    def UnaryStream(
        self,
        request: testproto.grpc.dummy_pb2.DummyRequest,
        context: _ServicerContext,
    ) -> typing.Union[collections.abc.Iterator[testproto.grpc.dummy_pb2.DummyReply], collections.abc.AsyncIterator[testproto.grpc.dummy_pb2.DummyReply]]:
        """UnaryStream"""
    @abc.abstractmethod
    def StreamUnary(
        self,
        request_iterator: _MaybeAsyncIterator[testproto.grpc.dummy_pb2.DummyRequest],
        context: _ServicerContext,
    ) -> typing.Union[testproto.grpc.dummy_pb2.DummyReply, collections.abc.Awaitable[testproto.grpc.dummy_pb2.DummyReply]]:
        """StreamUnary"""
    @abc.abstractmethod
    def StreamStream(
        self,
        request_iterator: _MaybeAsyncIterator[testproto.grpc.dummy_pb2.DummyRequest],
        context: _ServicerContext,
    ) -> typing.Union[collections.abc.Iterator[testproto.grpc.dummy_pb2.DummyReply], collections.abc.AsyncIterator[testproto.grpc.dummy_pb2.DummyReply]]:
        """StreamStream"""

def add_DummyServiceServicer_to_server(servicer: DummyServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
