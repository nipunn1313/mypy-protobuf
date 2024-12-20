"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import abc
import collections.abc
import google.protobuf.empty_pb2
import grpc
import grpc.aio
import sys
import testproto.test_pb2
import typing

if sys.version_info >= (3, 13):
    import typing as typing_extensions
else:
    import typing_extensions

_T = typing.TypeVar("_T")

class _MaybeAsyncIterator(collections.abc.AsyncIterator[_T], collections.abc.Iterator[_T], metaclass=abc.ABCMeta): ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore[misc, type-arg]
    ...

GRPC_GENERATED_VERSION: str
GRPC_VERSION: str
_SimpleServiceUnaryUnaryType = typing_extensions.TypeVar(
    '_SimpleServiceUnaryUnaryType',
    grpc.UnaryUnaryMultiCallable[
        google.protobuf.empty_pb2.Empty,
        testproto.test_pb2.Simple1,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        google.protobuf.empty_pb2.Empty,
        testproto.test_pb2.Simple1,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        google.protobuf.empty_pb2.Empty,
        testproto.test_pb2.Simple1,
    ],
)

_SimpleServiceUnaryStreamType = typing_extensions.TypeVar(
    '_SimpleServiceUnaryStreamType',
    grpc.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
)

_SimpleServiceNoCommentType = typing_extensions.TypeVar(
    '_SimpleServiceNoCommentType',
    grpc.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
    default=grpc.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
)

class SimpleServiceStub(typing.Generic[_SimpleServiceUnaryUnaryType, _SimpleServiceUnaryStreamType, _SimpleServiceNoCommentType]):
    """SimpleService"""

    @typing.overload
    def __init__(self: SimpleServiceStub[
        grpc.UnaryUnaryMultiCallable[
            google.protobuf.empty_pb2.Empty,
            testproto.test_pb2.Simple1,
        ],
        grpc.UnaryUnaryMultiCallable[
            testproto.test_pb2.Simple1,
            google.protobuf.empty_pb2.Empty,
        ],
        grpc.UnaryUnaryMultiCallable[
            testproto.test_pb2.Simple1,
            google.protobuf.empty_pb2.Empty,
        ],
    ], channel: grpc.Channel) -> None: ...

    @typing.overload
    def __init__(self: SimpleServiceStub[
        grpc.aio.UnaryUnaryMultiCallable[
            google.protobuf.empty_pb2.Empty,
            testproto.test_pb2.Simple1,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            testproto.test_pb2.Simple1,
            google.protobuf.empty_pb2.Empty,
        ],
        grpc.aio.UnaryUnaryMultiCallable[
            testproto.test_pb2.Simple1,
            google.protobuf.empty_pb2.Empty,
        ],
    ], channel: grpc.aio.Channel) -> None: ...

    UnaryUnary: _SimpleServiceUnaryUnaryType
    """UnaryUnary"""

    UnaryStream: _SimpleServiceUnaryStreamType
    """UnaryStream"""

    NoComment: _SimpleServiceNoCommentType

SimpleServiceAsyncStub: typing_extensions.TypeAlias = SimpleServiceStub[
    grpc.aio.UnaryUnaryMultiCallable[
        google.protobuf.empty_pb2.Empty,
        testproto.test_pb2.Simple1,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
    grpc.aio.UnaryUnaryMultiCallable[
        testproto.test_pb2.Simple1,
        google.protobuf.empty_pb2.Empty,
    ],
]

class SimpleServiceServicer(metaclass=abc.ABCMeta):
    """SimpleService"""

    @abc.abstractmethod
    def UnaryUnary(
        self,
        request: google.protobuf.empty_pb2.Empty,
        context: _ServicerContext,
    ) -> typing.Union[testproto.test_pb2.Simple1, collections.abc.Awaitable[testproto.test_pb2.Simple1]]:
        """UnaryUnary"""

    @abc.abstractmethod
    def UnaryStream(
        self,
        request: testproto.test_pb2.Simple1,
        context: _ServicerContext,
    ) -> typing.Union[google.protobuf.empty_pb2.Empty, collections.abc.Awaitable[google.protobuf.empty_pb2.Empty]]:
        """UnaryStream"""

    @abc.abstractmethod
    def NoComment(
        self,
        request: testproto.test_pb2.Simple1,
        context: _ServicerContext,
    ) -> typing.Union[google.protobuf.empty_pb2.Empty, collections.abc.Awaitable[google.protobuf.empty_pb2.Empty]]: ...

def add_SimpleServiceServicer_to_server(servicer: SimpleServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
