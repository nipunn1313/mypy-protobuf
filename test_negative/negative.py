"""
This code is intended to have mypy failures which we will ensure
show up in the output.
"""

import six

from typing import (
    List,
    Text,
)

from testproto.test_extensions2_pb2 import SeparateFileExtension
from testproto.test_pb2 import (
    DESCRIPTOR,
    Extensions1,
    Extensions2,
    FOO,
    Simple1,
    Simple2,
)
from testproto.test3_pb2 import OuterEnum, OuterEnumValue, SimpleProto3
from testproto.dot.com.test_pb2 import TestMessage

s = Simple1()
s.a_string = "Hello"

s2 = Simple1.FromString(s.SerializeToStringg())  # E:2.7 E:3.5

s3 = Simple1()
s3.ParseFromString(s)  # E:2.7 E:3.5

s4 = Simple1()
s4.CopyFrom(s.SerializeToString())  # E:2.7 E:3.5

s5 = Simple1()
l = []  # type: List[int]
l.extend(s5.a_repeated_string)  # E:2.7 E:3.5

tm = TestMessage(foo=55)  # E:2.7 E:3.5

e = FOO
e = 3  # E:2.7 E:3.5

# Proto2
s.HasField("garbage")  # E:2.7 E:3.5
s.HasField("a_repeated_string")  # E:2.7 E:3.5

# Proto3
s6 = SimpleProto3()
s6.HasField(u"garbage")  # E:2.7 E:3.5
s6.HasField(u"a_string")  # E:2.7 E:3.5
s6.HasField(u"outer_enum")  # E:2.7 E:3.5
s6.HasField(u"a_repeated_string")  # E:2.7 E:3.5

# Proto2
s.ClearField("garbage")  # E:2.7 E:3.5

# Proto3
s6.ClearField("garbage")  # E:2.7 E:3.5

# Proto2 WhichOneof
s.WhichOneof("garbage")  # E:2.7 E:3.5
a = 5
a = s.WhichOneof("a_oneof")  # E:2.7 E:3.5
b = s.WhichOneof("a_oneof")
s.HasField(b)  # allowed
simple2 = Simple2(a_string="abc")
simple2.HasField(b)  # E:2.7 E:3.5

# Proto3 WhichOneof
s6.WhichOneof("garbage")  # E:2.7 E:3.5
a3 = 5
a3 = s6.WhichOneof("a_oneof")  # E:2.7 E:3.5
b3 = s6.WhichOneof("a_oneof")
s6.HasField(b3)  # allowed
simple2.HasField(b3)  # E:2.7 E:3.5  - it's a text but not one of the literals

# Proto2 Extensions
an_int = 5
an_int = Extensions1.ext  # E:2.7 E:3.5
_ = s.Extensions[Extensions1.bad]  # E:2.7 E:3.5
_ = s.Extensions["foo"]  # E:2.7 E:3.5

# Overload WhichOneof
c = s6.WhichOneof("a_oneof")
c = s6.WhichOneof("b_oneof")  # E:2.7 E:3.5

# Message DESCRIPTOR should detect invalid access via instance or class:
SimpleProto3.DESCRIPTOR.Garbage()  # E:2.7 E:3.5
SimpleProto3().DESCRIPTOR.Garbage()  # E:2.7 E:3.5

# Enum DESCRIPTOR should detect invalid access:
OuterEnum.DESCRIPTOR.Garbage()  # E:2.7 E:3.5

# Module DESCRIPTOR should detect invalid access:
DESCRIPTOR.Garbage()  # E:2.7 E:3.5

# Enum value type should be an EnumValueType convertible to int
enum = OuterEnumValue(5)
enum = s6.a_outer_enum
as_int = 5
as_int = s6.a_outer_enum
s6.a_outer_enum.FOO  # E:2.7 E:3.5

# Name/Value/items should inherit value type from _EnumTypeWrapper
OuterEnum.Name(OuterEnumValue(5))
OuterEnum.Name(5)  # E:2.7 E:3.5
OuterEnum.Name(OuterEnum.Value("BAR"))
OuterEnum.Name(SimpleProto3.InnerEnum.Value("BAR"))  # E:2.7 E:3.5
OuterEnum.Name(OuterEnum.values()[0])
OuterEnum.Name(SimpleProto3.InnerEnum.values()[0])  # E:2.7 E:3.5
OuterEnum.Name(OuterEnum.items()[0][1])
OuterEnum.Name(SimpleProto3.InnerEnum.items()[0][1])  # E:2.7 E:3.5
