"""
Type-checking test for async_only GRPC stubs.

This module is run through mypy to validate that stubs generated with the
only_async flag have the correct types:
- Regular (non-generic) Stub class that only accepts grpc.aio.Channel
- No AsyncStub type alias (the stub itself is async-only)
- Servicer methods use AsyncIterator for client streaming (not _MaybeAsyncIterator)
- add_XXXServicer_to_server accepts grpc.aio.Server
"""

from typing import Awaitable
import grpc.aio
from testproto.grpc import dummy_pb2_grpc, dummy_pb2


class AsyncOnlyServicer(dummy_pb2_grpc.DummyServiceServicer):
    async def UnaryUnary(
        self,
        request: dummy_pb2.DummyRequest,
        context: grpc.aio.ServicerContext[dummy_pb2.DummyRequest, Awaitable[dummy_pb2.DummyReply]],
    ) -> dummy_pb2.DummyReply:
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "Not implemented")
        return dummy_pb2.DummyReply(value=request.value[::-1])


async def noop() -> None:
    """Don't actually run anything; this is just for type-checking."""
    stub = dummy_pb2_grpc.DummyServiceStub(channel=grpc.aio.insecure_channel("localhost:50051"))
    await stub.UnaryUnary(dummy_pb2.DummyRequest(value="test"))
