"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import google.protobuf.descriptor
import google.protobuf.message
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Simple3(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    A_STRING_FIELD_NUMBER: builtins.int
    a_string: builtins.str
    def __init__(
        self,
        *,
        a_string: builtins.str | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["a_string", b"a_string"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["a_string", b"a_string"]) -> None: ...

Global___Simple3: typing_extensions.TypeAlias = Simple3
