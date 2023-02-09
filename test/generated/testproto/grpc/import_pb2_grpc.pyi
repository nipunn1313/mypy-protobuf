"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import google.protobuf.empty_pb2
import grpc
import grpc.aio
import testproto.test_pb2
import typing

_T = typing.TypeVar('_T')

class _MaybeAsyncIterator(typing.AsyncIterator[_T], typing.Iterator[_T], metaclass=abc.ABCMeta):
    ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore
    ...

class SimpleServiceStub:
    """SimpleService"""

    def __init__(self, channel: typing.Union[grpc.Channel, grpc.aio.Channel]) -> None: ...
    UnaryUnary: grpc.UnaryUnaryMultiCallable[
        google.protobuf.empty_pb2.Empty,
        testproto.test_pb2.Simple1,
    ]
    """UnaryUnary"""
    UnaryStream: grpc.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ]
    """UnaryStream"""
    NoComment: grpc.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ]

class SimpleServiceAsyncStub:
    """SimpleService"""

    UnaryUnary: grpc.aio.UnaryUnaryMultiCallable[
        google.protobuf.empty_pb2.Empty,
        testproto.test_pb2.Simple1,
    ]
    """UnaryUnary"""
    UnaryStream: grpc.aio.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ]
    """UnaryStream"""
    NoComment: grpc.aio.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ]

class SimpleServiceServicer(metaclass=abc.ABCMeta):
    """SimpleService"""

    @abc.abstractmethod
    def UnaryUnary(
        self,
        request: google.protobuf.empty_pb2.Empty,
        context: _ServicerContext,
    ) -> typing.Union[testproto.test_pb2.Simple1, typing.Awaitable[testproto.test_pb2.Simple1]]:
        """UnaryUnary"""
    @abc.abstractmethod
    def UnaryStream(
        self,
        request: testproto.test_pb2.Simple1,
        context: _ServicerContext,
    ) -> typing.Union[google.protobuf.empty_pb2.Empty, typing.Awaitable[google.protobuf.empty_pb2.Empty]]:
        """UnaryStream"""
    @abc.abstractmethod
    def NoComment(
        self,
        request: testproto.test_pb2.Simple1,
        context: _ServicerContext,
    ) -> typing.Union[google.protobuf.empty_pb2.Empty, typing.Awaitable[google.protobuf.empty_pb2.Empty]]: ...

def add_SimpleServiceServicer_to_server(servicer: SimpleServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
