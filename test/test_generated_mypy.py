"""
This is a file which should mypy with success. See test_negative for
a file that should have failures.

This file contains a test to ensure that the test_negative failures
are the expected failures

These tests can be set up and run by the run_test.sh script
"""

import glob
import os
import pytest
import sys

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.message import Message

import testproto.test_pb2 as test_pb2
from testproto.reexport_pb2 import (
    SimpleProto3 as ReexportedSimpleProto3,
    FOO3 as ReexportedFOO3,
)
from testproto.test_extensions2_pb2 import SeparateFileExtension
from testproto.test_pb2 import (
    DESCRIPTOR,
    Extensions1,
    Extensions2,
    FOO,
    Name as NamingConflicts_Name,
    NamingConflicts,
    OuterEnum,
    PythonReservedKeywords,
    Simple1,
    Simple2,
)
from testproto.test3_pb2 import (
    BAR3,
    FOO3,
    OuterMessage3,
    SimpleProto3,
)
from testproto.test_extensions3_pb2 import (
    MessageOptionsTestMsg,
    scalar_option,
    repeated_scalar_option,
    enum_option,
    repeated_enum_option,
    msg_option,
    repeated_msg_option,
)
from testproto.Capitalized.Capitalized_pb2 import lower, lower2, Upper

from typing import (
    Any,
    NewType,
    Optional,
    Generator,
    Tuple,
    Type,
)

PY2 = sys.version_info < (3,)
PY3 = not PY2

UserId = NewType("UserId", int)


class Email(str):
    pass


def _is_summary(l):
    # type: (str) -> bool
    """Checks if the line is the summary line 'Found X errors in Y files (checked Z source files)'"""
    return l.startswith("Found ") and l.endswith("source files)\n")


def test_generate_mypy_matches():
    # type: () -> None
    if sys.version_info < (3, 0):
        return
    proto_files = glob.glob("proto/**/*.proto", recursive=True)
    assert len(proto_files) == 15  # Just a sanity check that all the files show up

    pyi_files = glob.glob("test/generated/**/*.pyi", recursive=True)
    assert (
        len(pyi_files) == 17
    )  # Should be higher - because grpc files generate extra pyis

    failure_check_results = []
    for fn in proto_files:
        assert fn.endswith(".proto")
        fn_split = fn.split(os.sep)  # Eg. [proto, testproto, dot.com, test.proto]
        assert fn_split[-1].endswith(".proto")
        last = fn_split[-1][: -len(".proto")] + "_pb2.pyi"  # Eg [test_pb2.proto]
        components = fn_split[1:-1]  # Eg. [testproto, dot.com]
        components = [
            c.replace(".", os.sep) for c in components
        ]  # Eg. [testproto, dot/com]
        components.append(last)  # Eg. [testproto, dot/com, test_pb2.proto]

        output = os.path.join("test", "generated", *components)

        assert os.path.exists(output)
        failure_check_results.append(output)
        if "grpc" in components:
            grpc_output = output[:-4] + "_grpc.pyi"
            assert os.path.exists(grpc_output)
            failure_check_results.append(grpc_output)

    # Make sure we checked everything
    assert len(failure_check_results) == len(pyi_files)


def test_generate_negative_matches():
    # type: () -> None
    """Confirm that the test_negative expected file matches an error for each line"""

    def grab_errors(filename):
        # type: (str) -> Generator[Tuple[str, int], None, None]
        for line in open(filename).readlines():
            if _is_summary(line):
                continue
            parts = line.split(":")
            yield parts[0], int(parts[1])

    def grab_expectations(filename, marker):
        # type: (str, str) -> Generator[Tuple[str, int], None, None]
        for idx, line in enumerate(open(filename).readlines()):
            if "#" in line and marker in line:
                yield filename, idx + 1

    errors_27 = set(grab_errors("test_negative/output.expected.2.7"))
    errors_38 = set(grab_errors("test_negative/output.expected.3.8"))

    expected_errors_27 = (
        set(grab_expectations("test_negative/negative.py", "E:2.7"))
        | set(grab_expectations("test_negative/negative_2.7.py", "E:2.7"))
        | set(grab_expectations("test/test_generated_mypy.py", "E:2.7"))
    )
    expected_errors_38 = set(
        grab_expectations("test_negative/negative.py", "E:3.8")
    ) | set(grab_expectations("test_negative/negative_3.8.py", "E:3.8"))

    assert errors_27 == expected_errors_27
    assert errors_38 == expected_errors_38

    # Some sanity checks to make sure we don't mess this up. Please update as necessary.
    assert len(errors_27) == 62
    assert len(errors_38) == 74


def test_func():
    # type: () -> None
    s = Simple1(a_string="hello")

    s = Simple1()
    s.a_string = "Hello"
    s.a_repeated_string.append("Hello")

    s2 = Simple1.FromString(s.SerializeToString())
    assert s2.a_string == "Hello"
    assert s2.A_STRING_FIELD_NUMBER == 1
    assert s2.USER_ID_FIELD_NUMBER == 21

    s3 = Simple1()
    s3.ParseFromString(s.SerializeToString())
    assert s3.a_string == "Hello"

    s4 = Simple1()
    s4.CopyFrom(s)
    assert s4.a_string == "Hello"

    l = lower2()
    l.upper.Lower.a = 2
    assert l == lower2(upper=Upper(Lower=lower(a=2)))


def test_enum():
    # type: () -> None
    e = FOO
    e = OuterEnum.Value("BAR")
    assert OuterEnum.Value("BAR") == 2
    assert OuterEnum.Name(e) == "BAR"
    assert OuterEnum.keys() == ["FOO", "BAR"]
    assert OuterEnum.values() == [1, 2]
    assert OuterEnum.items() == [("FOO", 1), ("BAR", 2)]

    # Make sure we can assure typing with a couple of techniques
    e2 = OuterEnum.Value("BAR")  # type: test_pb2.OuterEnum.V
    assert OuterEnum.Name(e2) == "BAR"
    e3 = OuterEnum.Value("BAR")  # type: OuterEnum.V
    assert OuterEnum.Name(e3) == "BAR"
    e4 = OuterEnum.Value("BAR")  # type: int
    assert OuterEnum.Name(e2) == "BAR"

    # Protobuf itself allows both unicode and bytes here.
    assert OuterEnum.Value(u"BAR") == OuterEnum.Value(b"BAR")


def test_enum_naming_conflicts():
    # type: () -> None
    assert NamingConflicts.Name(NamingConflicts_Name) == "Name"
    assert NamingConflicts.Value("Name") == 1
    assert NamingConflicts_Name == 1


def test_has_field_proto2():
    # type: () -> None
    """For HasField which is typed with Literal"""
    s = Simple1()
    s.a_string = "Hello"

    # Proto2 tests
    assert s.HasField(u"a_string")
    assert s.HasField("a_string")
    if PY2:
        assert s.HasField(b"a_string")
    assert not s.HasField("a_inner")
    assert not s.HasField("a_enum")
    assert not s.HasField("a_oneof")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(
        ValueError, match="Protocol message Simple1 has no field garbage."
    ):
        s_untyped.HasField("garbage")
    with pytest.raises(
        ValueError,
        match='Protocol message Simple1 has no singular "a_repeated_string" field',
    ):
        s_untyped.HasField("a_repeated_string")
    if PY3:
        with pytest.raises(TypeError, match="bad argument type for built-in operation"):
            s_untyped.HasField(b"a_string")

    none_err = (
        "bad argument type for built-in operation"
        if PY3
        else "expected string or Unicode object, NoneType found"
    )
    with pytest.raises(TypeError, match=none_err):
        s_untyped.HasField(None)


def test_has_field_proto3():
    # type: () -> None
    s = SimpleProto3()
    assert not s.HasField(u"outer_message")
    assert not s.HasField("outer_message")
    if PY2:
        assert not s.HasField(b"outer_message")
    assert not s.HasField("a_oneof")

    assert not s.HasField("an_optional_string")
    # synthetic oneof from optional field, see https://github.com/protocolbuffers/protobuf/blob/v3.12.0/docs/implementing_proto3_presence.md#updating-a-code-generator
    assert not s.HasField("_an_optional_string")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(
        ValueError, match="Protocol message SimpleProto3 has no field garbage."
    ):
        s_untyped.HasField(u"garbage")
    with pytest.raises(
        ValueError,
        match='Can\'t test non-optional, non-submessage field "SimpleProto3.a_string" for presence in proto3.',
    ):
        s_untyped.HasField(u"a_string")
    with pytest.raises(
        ValueError,
        match='Can\'t test non-optional, non-submessage field "SimpleProto3.a_outer_enum" for presence in proto3.',
    ):
        s_untyped.HasField("a_outer_enum")
    with pytest.raises(
        ValueError,
        match='Protocol message SimpleProto3 has no singular "a_repeated_string" field',
    ):
        s_untyped.HasField(u"a_repeated_string")
    if PY3:
        with pytest.raises(TypeError, match="bad argument type for built-in operation"):
            s_untyped.HasField(b"outer_message")

    none_err = (
        "bad argument type for built-in operation"
        if PY3
        else "expected string or Unicode object, NoneType found"
    )
    with pytest.raises(TypeError, match=none_err):
        s_untyped.HasField(None)


def test_clear_field_proto2():
    # type: () -> None
    """For ClearField which is typed with Literal"""
    s = Simple1()
    s.a_string = "Hello"

    # Proto2 tests
    s.ClearField(u"a_string")
    if PY2:
        s.ClearField(b"a_string")
    s.ClearField("a_string")
    s.ClearField("a_inner")
    s.ClearField("a_repeated_string")
    s.ClearField("a_oneof")
    s.ClearField(b"a_string")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(ValueError, match='Protocol message has no "garbage" field.'):
        s_untyped.ClearField("garbage")


def test_clear_field_proto3():
    # type: () -> None
    """For ClearField which is typed with Literal"""
    s = SimpleProto3()
    s.a_string = "Hello"

    # Proto2 tests
    s.ClearField(u"a_string")
    if PY2:
        s.ClearField(b"a_string")
    s.ClearField("a_string")
    s.ClearField("a_outer_enum")
    s.ClearField("outer_message")
    s.ClearField("a_repeated_string")
    s.ClearField("a_oneof")
    s.ClearField(b"a_string")
    s.ClearField("an_optional_string")
    # synthetic oneof from optional field
    s.ClearField("_an_optional_string")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(ValueError, match='Protocol message has no "garbage" field.'):
        s_untyped.ClearField("garbage")


def test_which_oneof_proto2():
    # type: () -> None
    s = Simple1()

    assert s.WhichOneof("a_oneof") is None
    s.a_oneof_1 = "hello"
    assert s.WhichOneof("a_oneof") == "a_oneof_1"
    assert s.WhichOneof(u"a_oneof") == "a_oneof_1"
    assert s.WhichOneof(b"a_oneof") == "a_oneof_1"
    assert type(s.WhichOneof("a_oneof")) == str
    field = s.WhichOneof("a_oneof")
    assert field is not None
    assert s.HasField(field)

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(
        ValueError, match='Protocol message has no oneof "garbage" field.'
    ):
        s_untyped.WhichOneof("garbage")


def test_which_oneof_proto3():
    # type: () -> None
    s = SimpleProto3()

    assert s.WhichOneof("a_oneof") is None
    s.a_oneof_1 = "hello"
    s.b_oneof_1 = "world"
    assert s.WhichOneof("a_oneof") == "a_oneof_1"
    assert s.WhichOneof(u"a_oneof") == "a_oneof_1"
    assert s.WhichOneof(b"a_oneof") == "a_oneof_1"
    assert type(s.WhichOneof("a_oneof")) == str

    field_a = s.WhichOneof("a_oneof")
    assert field_a is not None
    assert s.HasField(field_a)

    field_b = s.WhichOneof("b_oneof")
    assert field_b is not None
    assert s.HasField(field_b)

    # synthetic oneof from optional field
    assert s.WhichOneof("_an_optional_string") is None
    s.an_optional_string = "foo"
    field_aos = s.WhichOneof("_an_optional_string")
    assert field_aos is not None
    assert s.HasField(field_aos)

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(
        ValueError, match='Protocol message has no oneof "garbage" field.'
    ):
        s_untyped.WhichOneof("garbage")


def test_extensions_proto2():
    # type: () -> None
    s1 = Simple1()
    s2 = Simple2()

    assert isinstance(Extensions1.ext, FieldDescriptor)
    assert isinstance(Extensions2.foo, FieldDescriptor)
    assert isinstance(SeparateFileExtension.ext, FieldDescriptor)

    assert s1.HasExtension(Extensions1.ext) is False
    s1.ClearExtension(Extensions1.ext)

    e1 = s1.Extensions[Extensions1.ext]
    e1.ext1_string = "first extension"
    assert isinstance(e1, Extensions1)

    e2 = s1.Extensions[Extensions2.foo]
    e2.flag = True
    assert isinstance(e2, Extensions2)

    e3 = s2.Extensions[SeparateFileExtension.ext]
    e3.flag = True
    assert isinstance(e3, SeparateFileExtension)

    del s1.Extensions[Extensions2.foo]

    # Using __iter__, x is a FieldDescriptor but the type of the message that
    # s1.Extensions[x] yields is unknown (it could be any of the extension messages).
    # Hence, s1.Extensions[x] is typed as Any.
    for x in s1.Extensions:
        assert isinstance(x, FieldDescriptor)
        assert x.is_extension
        y = s1.Extensions[x]
        assert y.ext1_string == "first extension"

    assert Extensions1.ext in s1.Extensions

    assert len(s2.Extensions) == 1


def test_extensions_proto3():
    # type: () -> None
    assert (
        MessageOptionsTestMsg.DESCRIPTOR.GetOptions().Extensions[scalar_option]
        == "Hello world!"
    )
    assert MessageOptionsTestMsg.DESCRIPTOR.GetOptions().Extensions[
        repeated_scalar_option
    ] == ["A", "B", "C"]
    assert MessageOptionsTestMsg.DESCRIPTOR.GetOptions().Extensions[enum_option] == FOO3
    assert MessageOptionsTestMsg.DESCRIPTOR.GetOptions().Extensions[
        repeated_enum_option
    ] == [FOO3, BAR3]
    assert MessageOptionsTestMsg.DESCRIPTOR.GetOptions().Extensions[
        msg_option
    ] == OuterMessage3(a_string="Hello OuterMessage3")
    assert list(
        MessageOptionsTestMsg.DESCRIPTOR.GetOptions().Extensions[repeated_msg_option]
    ) == [
        OuterMessage3(a_string="Hello OuterMessage3 A"),
        OuterMessage3(a_string="Hello OuterMessage3 B"),
    ]


def test_constructor_proto2():
    # type: () -> None
    x = Simple2()  # It's OK to omit a required field from the constructor.
    assert not x.HasField("a_string")

    x = Simple2(a_string=None)  # It's OK to pass None for a required field.
    assert not x.HasField("a_string")


def test_message_descriptor_proto2():
    # type: () -> None
    assert Simple1().DESCRIPTOR.full_name == "test.Simple1"
    assert Simple1.DESCRIPTOR.full_name == "test.Simple1"


def test_message_descriptor_proto3():
    # type: () -> None
    assert SimpleProto3().DESCRIPTOR.full_name == "test3.SimpleProto3"
    assert SimpleProto3.DESCRIPTOR.full_name == "test3.SimpleProto3"


def test_reexport_identical():
    # type: () -> None
    assert SimpleProto3 is ReexportedSimpleProto3
    assert FOO3 is ReexportedFOO3


def test_enum_descriptor():
    # type: () -> None
    assert OuterEnum.DESCRIPTOR.name == "OuterEnum"


def test_module_descriptor():
    # type: () -> None
    assert DESCRIPTOR.name == "testproto/test.proto"


def test_mapping_type():
    # type: () -> None
    s = SimpleProto3()
    s.map_scalar[5] = "abcd"
    assert s.map_scalar[5] == "abcd"

    s.map_message[5].a_string = "hi"
    assert s.map_message[5] == OuterMessage3(a_string="hi")

    assert s.map_message.get_or_create(6) == OuterMessage3()
    assert s.map_message[6] == OuterMessage3()
    assert s.map_message.get_or_create(6) == OuterMessage3()

    s2 = SimpleProto3(
        map_scalar={5: "abcd"}, map_message={5: OuterMessage3(a_string="hi")}
    )


def test_casttype():
    # type: () -> None
    s = Simple1()
    s.user_id = UserId(33)
    assert s.user_id == 33
    s.email = Email("abcd@gmail.com")
    assert s.email == "abcd@gmail.com"
    s.email_by_uid[UserId(33)] = Email("abcd@gmail.com")


def test_reserved_keywords():
    # type: () -> None
    with pytest.raises(AttributeError, match="module.*has no attribute 'asdf'"):
        getattr(test_pb2, "asdf")

    # Confirm that "None" is a Message
    none_cls = getattr(test_pb2, "None")  # type: Type[test_pb2._r_None]
    none_instance = none_cls(valid=5)
    assert isinstance(none_instance, Message)

    # Confirm that messages and enums w/ reserved names type properly
    prk = PythonReservedKeywords(
        none=none_instance, valid=PythonReservedKeywords.valid_in_finally
    )
    assert prk.none.valid == 5
    assert prk.valid == PythonReservedKeywords.valid_in_finally
