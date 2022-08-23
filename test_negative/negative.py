"""
This code is intended to have mypy failures which we will ensure
show up in the output.
"""

from test.test_generated_mypy import Email, UserId
from typing import List, Text

from testproto.dot.com.test_pb2 import TestMessage
from testproto.test3_pb2 import OuterEnum, OuterMessage3, SimpleProto3
from testproto.test_extensions2_pb2 import SeparateFileExtension
from testproto.test_pb2 import (DESCRIPTOR, FOO, Extensions1, Extensions2,
                                PythonReservedKeywords, Simple1, Simple2)

s = Simple1()
s.a_string = "Hello"

s2 = Simple1.FromString(s.SerializeToStringg())  # E:2.7 E:3.8

s3 = Simple1()
s3.ParseFromString(s)  # E:2.7 E:3.8

s4 = Simple1()
s4.CopyFrom(s.SerializeToString())  # E:2.7 E:3.8

s5 = Simple1()
l: List[int] = []
l.extend(s5.a_repeated_string)  # E:2.7 E:3.8

tm = TestMessage(foo=55)  # E:2.7 E:3.8

e = FOO
e = 3  # E:2.7 E:3.8

# Proto2
s.HasField("garbage")  # E:2.7 E:3.8
s.HasField("a_repeated_string")  # E:2.7 E:3.8

# Proto3
s6 = SimpleProto3()
s6.HasField("garbage")  # E:2.7 E:3.8
s6.HasField("a_string")  # E:2.7 E:3.8
s6.HasField("outer_enum")  # E:2.7 E:3.8
s6.HasField("a_repeated_string")  # E:2.7 E:3.8

# Proto2
s.ClearField("garbage")  # E:2.7 E:3.8

# Proto3
s6.ClearField("garbage")  # E:2.7 E:3.8

# Proto2 WhichOneof
s.WhichOneof("garbage")  # E:2.7 E:3.8
a = 5
a = s.WhichOneof("a_oneof")  # E:2.7 E:3.8
b = s.WhichOneof("a_oneof")
assert b is not None
s.HasField(b)  # allowed
simple2 = Simple2(a_string="abc")
simple2.HasField(b)  # E:2.7 E:3.8

# WhichOneof should return optional str
var_of_type_str: str = ""
var_of_type_str = s.WhichOneof("a_oneof")  # E:2.7 E:3.8

# Proto3 WhichOneof
s6.WhichOneof("garbage")  # E:2.7 E:3.8
a3 = 5
a3 = s6.WhichOneof("a_oneof")  # E:2.7 E:3.8
b3 = s6.WhichOneof("a_oneof")
assert b3 is not None
s6.HasField(b3)  # allowed
simple2.HasField(b3)  # E:2.7 E:3.8  - it's a text but not one of the literals

# Proto2 Extensions
an_int = 5
an_int = Extensions1.ext  # E:2.7 E:3.8
_ = s.Extensions[Extensions1.bad]  # E:2.7 E:3.8
e1 = s.Extensions[Extensions1.ext]
e1.foo = 4  # E:2.7 E:3.8
e1 = s.Extensions[Extensions2.foo]  # E:2.7 E:3.8
# The following 5 extension lines will error once we undo some compat
# changes to typeshed a few months after the 1.24 release
# See https://github.com/python/typeshed/pull/4833
_ = s.Extensions["foo"]  # E:2.7 E:3.8
_ = s.Extensions[SeparateFileExtension.ext]  # E:2.7 E:3.8
_ = SeparateFileExtension.ext in s.Extensions  # E:2.7 E:3.8
del s.Extensions[SeparateFileExtension.ext]  # E:2.7 E:3.8
s.HasExtension(SeparateFileExtension.ext)  # E:2.7 E:3.8
simple2.ClearExtension(Extensions1.ext)  # E:2.7 E:3.8


for x in s.Extensions:
    pass
x = 4  # E:2.7 E:3.8

# Overload WhichOneof
c = s6.WhichOneof("a_oneof")
c = s6.WhichOneof("b_oneof")  # E:2.7 E:3.8

# Message DESCRIPTOR should detect invalid access via instance or class:
SimpleProto3.DESCRIPTOR.Garbage()  # E:2.7 E:3.8
SimpleProto3().DESCRIPTOR.Garbage()  # E:2.7 E:3.8

# Enum DESCRIPTOR should detect invalid access:
OuterEnum.DESCRIPTOR.Garbage()  # E:2.7 E:3.8

# Module DESCRIPTOR should detect invalid access:
DESCRIPTOR.Garbage()  # E:2.7 E:3.8

# Enum value type should be an EnumValueType convertible to int
enum = OuterEnum.V(5)
enum = s6.a_outer_enum
as_int = 5
as_int = s6.a_outer_enum
s6.a_outer_enum.FOO  # E:2.7 E:3.8

# Name/Value/items should inherit value type from _EnumTypeWrapper
OuterEnum.Name(OuterEnum.V(5))
OuterEnum.Name(5)  # E:2.7 E:3.8
OuterEnum.Name(OuterEnum.Value("BAR"))
OuterEnum.Name(SimpleProto3.InnerEnum.Value("BAR"))  # E:2.7 E:3.8
OuterEnum.Name(OuterEnum.values()[0])
OuterEnum.Name(SimpleProto3.InnerEnum.values()[0])  # E:2.7 E:3.8
OuterEnum.Name(OuterEnum.items()[0][1])
OuterEnum.Name(SimpleProto3.InnerEnum.items()[0][1])  # E:2.7 E:3.8

# Map field does not have get_or_create when mapping to a scalar type
s7 = SimpleProto3()
s7.map_scalar.get_or_create(0)  # E:2.7 E:3.8
# Incorrect key type should error
s7.map_scalar.get("abcd")  # E:2.7 E:3.8
s7.map_message.get("abcd")  # E:2.7 E:3.8
# Incorrect value type should error
map_val = 5
map_val = s7.map_scalar.get(0)  # E:2.7 E:3.8
map_val = s7.map_message.get(0)  # E:2.7 E:3.8
# Incorrect constructor type should error
s7 = SimpleProto3(map_scalar={"abcd": 5}, map_message={"abcd": "abcd"})  # E:2.7 E:3.8

# Castable types are typed as their cast, not the base type
s8 = Simple1()
s8.user_id = 55  # E:2.7 E:3.8
s8.email = "abcd@gmail.com"  # E:2.7 E:3.8
s8.email_by_uid[55] = "abcd@gmail.com"  # E:2.7 E:3.8
s8.email_by_uid[UserId(55)] = "abcd@gmail.com"  # E:2.7 E:3.8
s8.email_by_uid[55] = Email("abcd@gmail.com")  # E:2.7 E:3.8
s8 = Simple1(
    user_id=55,  # E:2.7 E:3.8
    email="abcd@gmail.com",  # E:2.7 E:3.8
    email_by_uid={55: "abcd@gmail.com"},  # E:2.7 E:3.8
)

# Should not reexport inner.proto, since it doesn't have public tag.
from testproto.reexport_pb2 import Inner  # E:2.7 E:3.8

# In proto2 - you can pass in None for primitive, but not in proto3
Simple2(a_string=None)
OuterMessage3(a_string=None)  # E:2.7 E:3.8

# Repeated scalar fields are not assignable only extendable
s9 = Simple1()
s10 = Simple1()
s9.a_repeated_string = s10.a_repeated_string  # E:2.7 E:3.8
s9.rep_inner_enum = s10.rep_inner_enum  # E:2.7 E:3.8

# Some reserved keywored testing
# Confirm that messages and enums w/ reserved names type properly
PythonReservedKeywords().none.valid
PythonReservedKeywords().none.invalid  # E:2.7 E:3.8
# Enum should be int, even on enum with invalid name
assert PythonReservedKeywords().valid == PythonReservedKeywords.valid_in_finally
a_string = "hi"
a_string = PythonReservedKeywords().valid  # E:2.7 E:3.8
