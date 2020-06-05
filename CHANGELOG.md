## Upcoming

- Update required mypy version to 0.780 (picks up new typeshed annotations)

## 1.21

- Support for module descriptor.
- Update mangling from `global__` to `message__`
- Split EnumValue from EnumTypeWrapper to fix message typing. Enforces that constructing
an enum value must happen via a NewType wrapper to the int.

Example:
```
enum ProtoEnum {
    FIRST = 1;
    SECOND = 2;
}

mesage ProtoMsg {
    ProtoEnum enum = 1;
}
```
Generated Before:
```
class ProtoEnum(object):
    @classmethod
    def Value(cls, name: str) -> ProtoEnum

class ProtoMsg(Message):
    def __init__(self, enum: ProtoEnum) -> None
```
Generated After:
```
ProtoEnumValue = NewType('ProtoEnumValue', int)
class ProtoEnum(object):
    @classmethod
    def Value(cls, name: str) -> ProtoEnumValue
    
class ProtoMsg(Message):
    def __init__(self, enum: ProtoEnumValue) -> None
```
Migration Guide (with example calling code)
Before
```
from msg_pb2 import ProtoEnum, ProtoMsg

def make_proto_msg(enum: ProtoEnum) -> ProtoMsg:
    return ProtoMsg(enum)
make_proto_msg(ProtoMsg.FIRST)
```
After
```
from msg_pb2 import ProtoEnum, ProtoMsg

def make_proto_msg(enum: 'msg_pb2.ProtoEnumValue') -> ProtoMsg:
    return ProtoMsg(enum)
make_proto_msg(ProtoMsg.FIRST)
```

- Use inline-style rather than comment-style typing in the pyi file
- Remove MergeFrom/CopyFrom from generated code as it is in the Message superclass

## 1.20

- Black code formatting
- Fix message/field name aliasing when field name matches a message/enum name

## 1.19

- Allow omitting required proto2 fields from constructor parameters
- Support and testing for python 3.8
- Support for python-protobuf to 3.11.3

## 1.18

- Use `entry_points:console_scripts` to support long paths to the python interpreter

## 1.17

- Update to newer mypy version - including minor changes to typeshed

## 1.16

- Absolute path to necessary python
- Add forward reference string literal support for enums
- Alias builtin types to avoid collision with field name

## 1.15

- Add `class` to set of python keywords

## 1.14

- Add `Message.DESCRIPTOR`


## Older changelogs not available. Check git log if you need them!
