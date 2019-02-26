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

from test.proto.test_pb2 import FOO, OuterEnum, Simple1
from test.proto.test3_pb2 import SimpleProto3
from test.proto.Capitalized.Capitalized_pb2 import lower, lower2, Upper

from typing import Any

def test_generate_mypy_matches():
    # type: () -> None
    proto_files = (
        glob.glob('proto/test/proto/*.proto') +
        glob.glob('proto/test/proto/*/*.proto')
    )
    assert len(proto_files) == 8  # Just a sanity check that all the files show up

    failures = []
    for fn in proto_files:
        fn_split = fn.split(os.sep)  # Eg. [proto, test, proto, test.proto]
        fn_split = fn_split[1:]  # Eg. [test, proto, test.proto]
        assert fn_split[-1].endswith('.proto')
        fn_split[-1] = fn_split[-1][:-len('.proto')] + '_pb2.pyi'  # Eg [test, proto, test_pb2.proto]

        output = os.path.join(*fn_split)

        fn_split[-1] += '.expected'  # Eg [test, proto, test_pb2.proto.expected]

        expected = os.path.join(*fn_split)

        assert os.path.exists(output)

        output_contents = open(output).read()
        expected_contents = open(expected).read() if os.path.exists(expected) else None

        if output_contents != expected_contents:
            open(expected, "w").write(output_contents)
            failures.append(("%s doesn't match %s. This test will copy it over." % (output, expected)))

    if failures:
        raise Exception(str(failures))

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

    e = FOO
    e = OuterEnum.Value('BAR')

    l = lower2()
    l.upper.Lower.a = 2
    assert l == lower2(upper=Upper(Lower=lower(a=2)))

def test_has_field_proto2():
    # type: () -> None
    """For HasField which is typed with Literal"""
    s = Simple1()
    s.a_string = "Hello"

    # Proto2 tests
    assert s.HasField(u"a_string")
    assert s.HasField("a_string")
    assert not s.HasField("a_inner")
    assert not s.HasField("a_enum")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(ValueError, match="Unknown field garbage."):
        s_untyped.HasField("garbage")
    with pytest.raises(ValueError, match='Protocol message has no singular "a_repeated_string" field'):
        s_untyped.HasField("a_repeated_string")
    if six.PY3:
        with pytest.raises(TypeError, match='bad argument type for built-in operation'):
            s_untyped.HasField(b"a_string")

def test_has_field_proto3():
    # type: () -> None
    s = SimpleProto3()
    assert not s.HasField(u"outer_message")
    assert not s.HasField("outer_message")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(ValueError, match="Unknown field garbage."):
        s_untyped.HasField(u"garbage")
    with pytest.raises(ValueError, match='Can\'t test non-submessage field "a_string" for presence in proto3.'):
        s_untyped.HasField(u"a_string")
    with pytest.raises(ValueError, match='Can\'t test non-submessage field "outer_enum" for presence in proto3.'):
        s_untyped.HasField("outer_enum")
    with pytest.raises(ValueError, match='Protocol message has no singular "a_repeated_string" field'):
        s_untyped.HasField(u"a_repeated_string")
    if six.PY3:
        with pytest.raises(TypeError, match='bad argument type for built-in operation'):
            s_untyped.HasField(b"outer_message")

def test_clear_field_proto2():
    # type: () -> None
    """For ClearField which is typed with Literal"""
    s = Simple1()
    s.a_string = "Hello"

    # Proto2 tests
    if six.PY3:
        s.ClearField(u"a_string")
    else:
        s.ClearField(b"a_string")
    s.ClearField("a_string")
    s.ClearField("a_inner")
    s.ClearField("a_repeated_string")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(ValueError, match='Protocol message has no "garbage" field.'):
        s_untyped.ClearField("garbage")
    # This error message is very inconsistent w/ how HasField works
    with pytest.raises(TypeError, match='field name must be a string'):
        if six.PY2:
            s_untyped.ClearField(u"a_string")
        else:
            s_untyped.ClearField(b"a_string")

def test_clear_field_proto3():
    # type: () -> None
    """For ClearField which is typed with Literal"""
    s = SimpleProto3()
    s.a_string = "Hello"

    # Proto2 tests
    if six.PY3:
        s.ClearField(u"a_string")
    else:
        s.ClearField(b"a_string")
    s.ClearField("a_string")
    s.ClearField("outer_enum")
    s.ClearField("outer_message")
    s.ClearField("a_repeated_string")

    # Erase the types to verify that incorrect inputs fail at runtime
    # Each test here should be duplicated in test_negative to ensure mypy fails it too
    s_untyped = s  # type: Any
    with pytest.raises(ValueError, match='Protocol message has no "garbage" field.'):
        s_untyped.ClearField("garbage")
    # This error message is very inconsistent w/ how HasField works
    with pytest.raises(TypeError, match='field name must be a string'):
        if six.PY2:
            s_untyped.ClearField(u"a_string")
        else:
            s_untyped.ClearField(b"a_string")
