"""
Type-checking test for async_only GRPC stubs.

This module is run through mypy to validate that stubs generated with the
only_async flag have the correct types:
- Regular (non-generic) Stub class that only accepts grpc.aio.Channel
- No AsyncStub type alias (the stub itself is async-only)
- Servicer methods use AsyncIterator for client streaming (not _MaybeAsyncIterator)
- add_XXXServicer_to_server accepts grpc.aio.Server
"""

from testproto.grpc.dummy_pb2_grpc import DummyServiceServicer


class AsyncOnlyServicer(DummyServiceServicer):
    """Test servicer for async_only stubs - intentionally incomplete."""

    pass
