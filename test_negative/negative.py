"""
This code is intended to have mypy failures which we will ensure
show up in the output.
"""

from typing import (
    List,
    Text,
)

from test.proto.test_pb2 import FOO, Simple1

s = Simple1()
s.a_string = "Hello"

s2 = Simple1.FromString(s.SerializeToStringg())  # failure
assert s2.a_string == "Hello"

s3 = Simple1()
s3.ParseFromString(s)  # will be a failure once typeshed marks this as taking `bytes`
assert s3.a_string == "Hello"

s4 = Simple1()
s4.CopyFrom(s.SerializeToString())  # failure
assert s4.a_string == "Hello"

s5 = Simple1()
s5.a_repeated_string.append("World")
l = []  # type: List[int]
l.extend(s5.a_repeated_string)

e = FOO
e = 3  # failure
