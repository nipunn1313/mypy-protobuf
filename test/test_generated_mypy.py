"""
This file serves two purposes
1) Run a test which ensures that mypy is producing the expected output. For
developer convenience, in the case which it doesn't, it'll copy over the
output to the expected output, so you can view the output diff in your
code reviews. This will fail in CI if there is any inconsistency.

2) This is a file which should mypy with success. See test_negative for
a file that should have failures.
"""

import glob
import os
import pytest
import six

import test.proto.test_pb2 as test_pb2
from test.proto.test_pb2 import DESCRIPTOR, FOO, OuterEnum, Simple1, Simple2
from test.proto.test3_pb2 import SimpleProto3
from test.proto.Capitalized.Capitalized_pb2 import lower, lower2, Upper

from typing import Any

MYPY = False
if MYPY:
    from test.proto.test_pb2 import OuterEnumValue


def _is_summary(l):
    # type: (str) -> bool
    """Checks if the line is the summary line 'Found X errors in Y files (checked Z source files)'"""
    return l.startswith("Found ") and l.endswith("source files)\n")


def test_generate_mypy_matches():
    # type: () -> None
    proto_files = glob.glob("proto/test/proto/*.proto") + glob.glob(
        "proto/test/proto/*/*.proto"
    )
    assert len(proto_files) == 9  # Just a sanity check that all the files show up

    failures = []
    for fn in proto_files:
        assert fn.endswith(".proto")
        fn_split = fn.split(os.sep)  # Eg. [proto, test, proto, test.com, test.proto]
        assert fn_split[-1].endswith(".proto")
        last = fn_split[-1][: -len(".proto")] + "_pb2.pyi"  # Eg [test_pb2.proto]
        components = fn_split[1:-1]  # Eg. [test, proto, test.com]
        components = [
            c.replace(".", os.sep) for c in components
        ]  # Eg. [test, proto, test/com]
        components.append(last)  # Eg. [test, proto, test/com, test_pb2.proto]

        output = os.path.join(*components)

        components[
            -1
        ] += ".expected"  # Eg [test, proto, test/com, test_pb2.proto.expected]

        expected = os.path.join(*components)

        assert os.path.exists(output)

        output_contents = open(output).read()
        expected_contents = open(expected).read() if os.path.exists(expected) else None

        if output_contents != expected_contents:
            open(expected, "w").write(output_contents)
            failures.append(
                (
                    "%s doesn't match %s. This test will copy it over. Please rerun"
                    % (output, expected)
                )
            )

    if failures:
        raise Exception(str(failures))


def test_generate_negative_matches():
    # type: () -> None
    """Confirm that the test_negative expected file matches an error for each line"""
    test_negative_lines = open("test_negative/negative.py").readlines()
    # Grab the line number of the failures
    errors_27 = set(
        int(l.split(":")[1])
        for l in open("test_negative/output.expected.2.7").readlines()
        if not _is_summary(l)
    )
    errors_35 = set(
        int(l.split(":")[1])
        for l in open("test_negative/output.expected.3.5").readlines()
        if not _is_summary(l)
    )

    expected_errors_27 = set(
        idx + 1 for idx, line in enumerate(test_negative_lines) if "E:2.7" in line
    )
    expected_errors_35 = set(
        idx + 1 for idx, line in enumerate(test_negative_lines) if "E:3.5" in line
    )

    assert errors_27 == expected_errors_27
    assert errors_35 == expected_errors_35

    # Some sanity checks to make sure we don't mess this up. Please update as necessary.
    assert len(errors_27) == 30
    assert len(errors_35) == 30


def test_func():
    # type: () -> None
    s = Simple1(a_string="hello")

    s = Simple1()
    s.a_string = "Hello"
    s.a_repeated_string.append("Hello")

    s2 = Simple1.FromString(s.SerializeToString())
    assert s2.a_string == "Hello"

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
    e2 = OuterEnum.Value("BAR")  # type: test_pb2.OuterEnumValue
    assert OuterEnum.Name(e2) == "BAR"
    e3 = OuterEnum.Value("BAR")  # type: OuterEnumValue
    assert OuterEnum.Name(e3) == "BAR"
    e4 = OuterEnum.Value("BAR")  # type: int
    assert OuterEnum.Name(e2) == "BAR"


def test_has_field_proto2():
    # type: () -> None
    """For HasField which is typed with Literal"""
    s = Simple1()
    s.a_string = "Hello"

    # Proto2 tests
    assert s.HasField(u"a_string")
    assert s.HasField("a_string")
    if six.PY2:
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
    if six.PY3:
        with pytest.raises(TypeError, match="bad argument type for built-in operation"):
            s_untyped.HasField(b"a_string")


def test_has_field_proto3():
    # type: () -> None
    s = SimpleProto3()
    assert not s.HasField(u"outer_message")
    assert not s.HasField("outer_message")
    if six.PY2:
        assert not s.HasField(b"outer_message")
    assert not s.HasField("a_oneof")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(
        ValueError, match="Protocol message SimpleProto3 has no field garbage."
    ):
        s_untyped.HasField(u"garbage")
    with pytest.raises(
        ValueError,
        match='Can\'t test non-submessage field "SimpleProto3.a_string" for presence in proto3.',
    ):
        s_untyped.HasField(u"a_string")
    with pytest.raises(
        ValueError,
        match='Can\'t test non-submessage field "SimpleProto3.a_outer_enum" for presence in proto3.',
    ):
        s_untyped.HasField("a_outer_enum")
    with pytest.raises(
        ValueError,
        match='Protocol message SimpleProto3 has no singular "a_repeated_string" field',
    ):
        s_untyped.HasField(u"a_repeated_string")
    if six.PY3:
        with pytest.raises(TypeError, match="bad argument type for built-in operation"):
            s_untyped.HasField(b"outer_message")


def test_clear_field_proto2():
    # type: () -> None
    """For ClearField which is typed with Literal"""
    s = Simple1()
    s.a_string = "Hello"

    # Proto2 tests
    s.ClearField(u"a_string")
    if six.PY2:
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
    if six.PY2:
        s.ClearField(b"a_string")
    s.ClearField("a_string")
    s.ClearField("a_outer_enum")
    s.ClearField("outer_message")
    s.ClearField("a_repeated_string")
    s.ClearField("a_oneof")
    s.ClearField(b"a_string")

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
    assert s.HasField(s.WhichOneof("a_oneof"))

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
    assert s.HasField(s.WhichOneof("a_oneof"))
    assert s.HasField(s.WhichOneof("b_oneof"))

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(
        ValueError, match='Protocol message has no oneof "garbage" field.'
    ):
        s_untyped.WhichOneof("garbage")


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


def test_enum_descriptor():
    # type: () -> None
    assert OuterEnum.DESCRIPTOR.name == "OuterEnum"


def test_module_descriptor():
    # type: () -> None
    assert DESCRIPTOR.name == "test/proto/test.proto"
