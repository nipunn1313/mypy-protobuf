"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import sys
import typing

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class NoPackage(google.protobuf.message.Message):
    """Intentionally don't set a package - just to make sure we can handle it."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___NoPackage = NoPackage

@typing.final
class NoPackage2(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    NP_FIELD_NUMBER: builtins.int
    NP_REP_FIELD_NUMBER: builtins.int
    @property
    def np(self) -> global___NoPackage: ...
    @property
    def np_rep(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___NoPackage]: ...
    def __init__(
        self,
        *,
        np: global___NoPackage | None = ...,
        np_rep: collections.abc.Iterable[global___NoPackage] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["np", b"np"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["np", b"np", "np_rep", b"np_rep"]) -> None: ...

global___NoPackage2 = NoPackage2
