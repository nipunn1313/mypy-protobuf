## Upcoming

## 3.3.0

- Prefer (mypy_protobuf.options).casttype to (mypy_protobuf.casttype)
    - Allows us to use a single extension number
    - Applies to casttype,keytype,valuetype
    - Deprecate (but still support) the old-style extension
- Prefer importing from `typing` over `typing_extensions` on new enough python versions
- Support emitting module docstrings
- Make generated code flake8 compatible
- Convert extensions.proto to proto3
- Drop support for Python 3.6 [EOL]
- Bump to grpc-stubs 1.24.7
- Require protobuf 3.19.4
- Bump support to mypy 0.941
- Use PEP 604 Union syntax `X | None` rather than `Optional[X]`
- Moved from dropbox/mypy-protobuf to nipunn1313/mypy-protobuf
  - Nipunn is the primary maintainer and plans to continue maintenance!

## 3.2.0

- Remove unnecessary `...` in generated files.
- Reorder/reference enum classes to avoid forward references.
- Support `*_FIELD_NUMBER` for extensions
- Bump types-protobuf dependency to 3.19
- Require protobuf 3.19.3
- Support DESCRIPTOR: ServiceDescriptor in py generic services
- More accurately represent method names in py generic services (done -> callback, self -> inst)
- More accurately represent method names in grpc services (`request` -> `request_iterator`)
- Internal: Get tests to pass on pure-python protobuf impl (minor semantic differences)
- Internal: Bump pyright in testing to 1.1.206
- Internal: Use stubtest to validate generated stubs match generated runtime

## 3.1.0

- Require protobuf 3.19.1
- Change `EnumTypeWrapper.V` to `EnumTypeWrapper.ValueType` per https://github.com/protocolbuffers/protobuf/pull/8182.
Will allow for unquoted annotations starting with protobuf 3.20.0. `.V` will continue to work for the foreseeable
future for backward compatibility.
- suppress pyright warning reportSelfClsParameterName when a proto field is named `self`
- Allow optional constructor keywords for primitive field types in proto3, following this [chart](https://github.com/protocolbuffers/protobuf/blob/master/docs/field_presence.md#presence-in-proto3-apis).
- Reorder Enum helper classes to eliminate pycharm errors

## 3.0.0

- Drop support for targeting python 2.7
- Generate py3 specific syntax for unicode strings (`""` rather than `u""`)
- Now requires protobuf 3.18.0
- Handle escaping properly in docstrings and attribute strings (#296)
- Use three-digit version number 3.0.0 for minor and patch releases
- Codify pyright support in README

## 2.10

- Switch from setup.py to pyproject.toml and setup.cfg per https://packaging.python.org/tutorials/packaging-projects/
- Remove dependency on grpcio-tools. mypy-protobuf doesn't need it to run. It's only needed to run mypy afterward.
- Avoid relative imports in `_grpc_pb2.pyi` stubs. grpc stubs themselves don't use relative imports, nor `__init__.py` files
- Use `"""` docstring style comments in generated code rather than `#` style so it shows up in IDEs.
- Disambiguate messages from reserved python keywords (eg `None`) with prefix `_r_` rather than `__` - since `__` is considered private.
- Bump tests to use pyright 1.1.169, types-protobuf 3.17.4, pytest 6.2.5, grpc-stubs 1.24.7, grpcio-tools 1.40.0
- Since upstream protobuf has dropped support with 3.18.0, 2.10 will be the last mypy-protobuf that supports targeting python 2.7. Updated docs for this.

## 2.9

- [Rename master branch to main](https://github.com/github/renaming)
- Make `install_requires` requirements for grpcio-tools and types-protobuf use >=

## 2.8

- Propagate comments from .proto files to .pyi files
- Add protobuf type stubs to the setup requirements
- Fix [#239](https://github.com/nipunn1313/mypy-protobuf/issues/239) Remove type: ignore used in enum by pulling `V` into a separate class.
- Use pytest 6.2.4 for internal test suites on python3
- Remove `protoc_gen_mypy.bat` as the entry-points method creates protoc-gen-mypy.exe. Add test confirming.

## 2.7

- Fix [#244](https://github.com/nipunn1313/mypy-protobuf/issues/244) - support extensions defined at module scope with proper types, matching extensions defined within Messages. See [`_ExtensionDict`](https://github.com/python/typeshed/blob/4765978f6ceeb24e10bdf93c0d4b72dfb35836d4/stubs/protobuf/google/protobuf/internal/extension_dict.pyi#L9)
```proto
extend google.protobuf.MessageOptions {
   string test_message_option = 51234;
}
```
```python
# Used to generate
test_message_option: google.protobuf.descriptor.FieldDescriptor = ...

# Now generates
test_message_option: google.protobuf.internal.extension_dict._ExtensionFieldDescriptor[google.protobuf.descriptor_pb2.MessageOptions, typing.Text] = ...
```
Fix repeated extensions as well - to generate RepeatedScalarFieldContainer and RepeatedCompositeFieldContainer
- Now requires [types-protobuf](https://pypi.org/project/types-protobuf/) 3.17.3
- Fix [#238](https://github.com/nipunn1313/mypy-protobuf/issues/238) - handling enum variants that name conflict with EnumTypeWrapper methods
- Improve mypy-protobuf testsuite expected-errors file to make insertions/deletions easier to code review
- Fix [#227](https://github.com/nipunn1313/mypy-protobuf/issues/227) - improve support for messages/enums with python reserved keyword names
- Order fields within a message in original .proto file order Previously, they were grouped by scalar/nonscalar. Remove
that grouping to make it a bit easier to correlate .proto files to .pyi files.

## 2.6

- Bump protoc support to 3.17.3
- Use latest python versions in tests (3.6.14 3.7.11 3.8.11 3.9.6)
- Support reserved names for message types. Previously generated invalid mypy.
```proto
message M {
  message None {}
  None none = 1;
}
```
- Support `protoc-gen-mypy -V` and `protoc-gen-mypy --version` to print version number
- Return `Optional[Literal[...]]` instead of `Literal[...]` from WhichOneof to support
cases in which none of the fields of the WhichOneof are set. See the following example.
```python
def hello(name: str) -> None: ...
n = proto.WhichOneof("name")
hello(n)  # Will now result in a mypy error.
assert n is not None
hello(n)  # Should work ok
```
- Bump mypy version to 0.910, utilizing stubs types-protobuf==0.1.14. See https://mypy-lang.blogspot.com/2021/05/the-upcoming-switch-to-modular-typeshed.html
- Bump grpcio version tested to 1.38.1 and grpc-stubs to 1.24.6
- Generate a `# type: ignore` for enum generated stubs to avoid circular dependency described in #214. Bandaid solution.

## 2.5

- Organized generated enum code to prevent definition ordering issues in Pyright-based linters
- Changed type generation for `grpcio` stubs to use the `MultiCallable` API ([see here](https://grpc.github.io/grpc/python/grpc.html#multi-callable-interfaces)) . This requires using the `grpc-stubs` typings for grpcio. This change should allow calling stub methods with common parameters (`timeout`, `metadata`, etc.) as well as calling methods on the `MultiCallable` object (e.g. `my_stub.MyRpcMethod.future()`).
- Update stubs to mark repeated scalar and repeated enum fields as read-only

## 2.4

- Add support for `_FIELD_NUMBER` generated fields on messages as specified [in the spec](https://developers.google.com/protocol-buffers/docs/reference/python-generated#fields)

## 2.3

- Fix CI caching across version updates.
- Added unit testing for EnumTypeWrapper.Value usage
- Reexport of top level enum values when using `import public`

## 2.2

- Fix bug where module level `DESCRIPTOR: FileDescriptor` was not being generated for files w public imports

## 2.1

- Fix crash when a import public reexport when dependent proto file is not listed on command line for generation

## 2.0

Non Backward Compatible Changes
- Dropping support for running mypy-protobuf in python <= 3.5. Note you can still generate stubs target-compatible to python2
- Type proto Enum values for as `MyEnum.V` rather than `MyEnumValue` for import ergonomics,
allowing the caller to import `MyEnum` rather than conditionally importing `MyEnumValue`
- Default disallow `None` as argument for primitive fields of constructors in proto3.
Provided `relax_strict_optional_primitives` flag to relax this strictness if you prefer.

New Features
- Support for `grpcio` stubs generation
- Allow `mypy_protobuf.py` to be run directly as a script
- Add support for proto's [`well_known_types`](https://developers.google.com/protocol-buffers/docs/reference/python-generated#wkt)
- Support message fields named `self` - by renaming the constructor's `self` to `self_`
- Rename extensions proto from `mypy/mypy.proto` to `mypy_protobuf/extensions.proto`
- Add support for mypy-proto extensions `mypy_protobuf.casttype`, `mypy_protobuf.keytype`, and `mypy_protobuf.valuetype`
- Add support for `import public` proto imports - by reexporting in generated code

Output Format
- Generate fully qualified references rather than mangling
- Import builtins library rather than mangling builtins
- Use fully qualified names rather than mangling imports
- Only mangle-alias top-level identifiers w/ `global___` to avoid conflict w/ fields of same name [previously was mangling inner messages as well]
- Add support for `readable_stubs` parameter for mangle-free output code w/o fully-qualified references to message.
(in many cases this is good enough and easier to read)
- Generate `arg: Optional[type] = ...` instead of `arg: Optional[type] = None`
- Avoid importing google.protobuf.message.Message unless it's needed

Internal Improvements
- Add support for python 3.9 to CI
- Update mypy-protobuf CI to target 3.8 rather than 3.5
- Inline mypy annotations, eliminate six, and remove `__future__` import in `mypy_protobuf_lib.py`
- Flatten directory structure (remove python subdirectory). Updated unreleased installation instructions.
- Deprecate and delete the go/ implementation

## 1.24

- Bump required mypy version to 0.800
- Bump required protobuf version to 3.14 (pi!!)
- Update the autogenerated `.pyi` file header to cite `mypy-protobuf`
- Reorganize mypy-protobuf testsuite files to more closely match autogeneration into a `generated` directory
- Remove incorrect `type___` prefixed alias for inner enum type wrappers
- Add support for extension fields in proto2 messages
- Overwrite typing for `Message.Extensions` mapping to support better type inference for proto2 message extensions
- Support `Message.HasExtension` and `Message.ClearExtension`
- Bump python-protobuf from 3.11.3 to 3.13.0
- Add support for optional proto3 fields
- Support ScalarMap and MessageMap generated types for map types in proto.  This will allow us to support `get_or_create`

```proto
message Message {
    map<int32, OuterMessage3> map_message = 17
}
```
and
```python
message.map_message.get_or_create(0)
```

Before (1.23)
```
main.py:4: error: "MutableMapping[str, Nested]" has no attribute "get_or_create"  [attr-defined]
```
After (1.24) - there is no error

## 1.23

- Inherit FromString from superclass Message - rather than re-generating here. Fixes bug
in python2 usage `google/protobuf/type_pb2.pyi:92: error: Argument 1 of "FromString" is incompatible with supertype "Message"; supertype defines the argument type as "ByteString"  [override]`

## 1.22

- Update tested/required mypy version to 0.780 (picks up new typeshed annotations). Includes improved typing/error messages on Message.

Before (mypy < 0.780):
```
test_negative/negative.py:26: error: Argument 1 to "CopyFrom" of "Message" has incompatible type "str"; expected "Message"
```
After (mypy >= 0.780:
```
test_negative/negative.py:26: error: Argument 1 to "CopyFrom" of "Message" has incompatible type "str"; expected "Simple1"
```
- Update generated EnumTypeWrapper to be instances of EnumTypeWrapper - for more consistency
with generated python code. Most caller code should not require mypy type changes. Egh
`ProtoEnum.Value('first')` should work either way.

Generated Before (in 1.21)
```python
class ProtoEnum(object):
    @classmethod
    def Value(cls, name: str) -> ProtoEnumValue
```

Generated After (in 1.22)
```python
ProtoEnum: _ProtoEnum
class _ProtoEnum(google.protobuf.EnumTypeWrapper):
    def Value(self, name: str) -> ProtoEnumValue
```
- Remove autogenerated EnumTypeWrapper methods that are redundant to the typeshed parent class. Added testing for these.

## 1.21

- Support for module descriptor.
- Update mangling from `global__` to `message__`
- Fix bug in message typing for nested enums. Split EnumValue from EnumTypeWrapper. Enforces that constructing
an enum value must happen via a NewType wrapper to the int.

Example:
```proto
enum ProtoEnum {
    FIRST = 1;
    SECOND = 2;
}

mesage ProtoMsg {
    ProtoEnum enum = 1;
}
```
Generated Before (in 1.20):
```python
class ProtoEnum(object):
    @classmethod
    def Value(cls, name: str) -> ProtoEnum

class ProtoMsg(Message):
    def __init__(self, enum: ProtoEnum) -> None
```
Generated After (in 1.21):
```python
ProtoEnumValue = NewType('ProtoEnumValue', int)
class ProtoEnum(object):
    @classmethod
    def Value(cls, name: str) -> ProtoEnumValue

class ProtoMsg(Message):
    def __init__(self, enum: ProtoEnumValue) -> None
```
Migration Guide (with example calling code)

Before (with 1.20)
```python
from msg_pb2 import ProtoEnum, ProtoMsg

def make_proto_msg(enum: ProtoEnum) -> ProtoMsg:
    return ProtoMsg(enum)
make_proto_msg(ProtoMsg.FIRST)
```
After (with 1.21)
```python
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
