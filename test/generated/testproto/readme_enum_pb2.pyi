"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _MyEnum:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _MyEnumEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_MyEnum.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    HELLO: _MyEnum.ValueType  # 0
    WORLD: _MyEnum.ValueType  # 1

class MyEnum(_MyEnum, metaclass=_MyEnumEnumTypeWrapper): ...

HELLO: MyEnum.ValueType  # 0
WORLD: MyEnum.ValueType  # 1
global___MyEnum: typing_extensions.TypeAlias = MyEnum
