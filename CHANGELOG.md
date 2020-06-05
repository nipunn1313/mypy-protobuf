## Upcoming

- Update required mypy version to 0.780 (picks up new typeshed annotations)

## 1.21

- Support for module descriptor.
- Update mangling from `global__` to `message__`
- Split EnumValue from EnumTypeWrapper to fix message typing. Enforces that constructing
an enum value must happen via a NewType wrapper to the int.
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
