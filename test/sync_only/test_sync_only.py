"""
Type-checking test for sync_only GRPC stubs.

This module is run through mypy to validate that stubs generated with the
only_sync flag have the correct types:
- Regular (non-generic) Stub class that only accepts grpc.Channel
- Servicer methods use Iterator for client streaming (not _MaybeAsyncIterator)
- add_XXXServicer_to_server accepts grpc.Server
"""

import grpc
from testproto.grpc import dummy_pb2, dummy_pb2_grpc


class AsyncOnlyServicer(dummy_pb2_grpc.DummyServiceServicer):
    def UnaryUnary(
        self,
        request: dummy_pb2.DummyRequest,
        context: grpc.ServicerContext,
    ) -> dummy_pb2.DummyReply:
        return dummy_pb2.DummyReply(value=request.value[::-1])


def noop() -> None:
    """Don't actually run anything; this is just for type-checking."""
    stub = dummy_pb2_grpc.DummyServiceStub(channel=grpc.insecure_channel("localhost:50051"))
    stub.UnaryUnary(dummy_pb2.DummyRequest(value="test"))
