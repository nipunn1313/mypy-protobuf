"""
Type-checking test for sync_only GRPC stubs.

This module is run through mypy to validate that stubs generated with the
only_sync flag have the correct types:
- Regular (non-generic) Stub class that only accepts grpc.Channel
- Servicer methods use Iterator for client streaming (not _MaybeAsyncIterator)
- add_XXXServicer_to_server accepts grpc.Server
"""

from testproto.grpc.dummy_pb2_grpc import DummyServiceServicer


class SyncOnlyServicer(DummyServiceServicer):
    """Test servicer for sync_only stubs - intentionally incomplete."""

    pass
