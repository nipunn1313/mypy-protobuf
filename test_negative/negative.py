"""
This code is intended to have mypy failures which we will ensure
show up in the output.
"""

import six

from typing import (
    List,
    Text,
)

from test.proto.test_pb2 import FOO, Simple1
from test.proto.test3_pb2 import SimpleProto3

s = Simple1()
s.a_string = "Hello"

s2 = Simple1.FromString(s.SerializeToStringg())  # E:2.7 E:3.5

s3 = Simple1()
s3.ParseFromString(s)  # will be a failure once typeshed marks this as taking `bytes`

s4 = Simple1()
s4.CopyFrom(s.SerializeToString())  # E:2.7 E:3.5

s5 = Simple1()
l = []  # type: List[int]
l.extend(s5.a_repeated_string)  # E:2.7 E:3.5

e = FOO
e = 3  # E:2.7 E:3.5

# Proto2
s.HasField("garbage")  # E:2.7 E:3.5
s.HasField("a_repeated_string")  # E:2.7 E:3.5
if six.PY3:
    s.HasField(b"a_string")  # E:3.5

# Proto3
s6 = SimpleProto3()
s6.HasField(u"garbage")  # E:2.7 E:3.5
s6.HasField(u"a_string")  # E:2.7 E:3.5
s6.HasField(u"outer_enum")  # E:2.7 E:3.5
s6.HasField(u"a_repeated_string")  # E:2.7 E:3.5
if six.PY3:
    s6.HasField(b"outer_message")  # E:3.5

# Proto2
s.ClearField("garbage")  # E:2.7 E:3.5
# This error message is very inconsistent w/ how HasField works
if six.PY2:
    s.ClearField(u"a_string")  # E:2.7
else:
    s.ClearField(b"a_string")  # E:3.5

# Proto3
s6.ClearField("garbage")  # E:2.7 E:3.5
# This error message is very inconsistent w/ how HasField works
if six.PY2:
    s6.ClearField(u"a_string")  # E:2.7
else:
    s6.ClearField(b"a_string")  # E:3.5
