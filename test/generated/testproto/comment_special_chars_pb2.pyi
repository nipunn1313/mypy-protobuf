"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import google.protobuf.descriptor
import google.protobuf.message
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Test(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    A_FIELD_NUMBER: builtins.int
    B_FIELD_NUMBER: builtins.int
    C_FIELD_NUMBER: builtins.int
    D_FIELD_NUMBER: builtins.int
    E_FIELD_NUMBER: builtins.int
    F_FIELD_NUMBER: builtins.int
    G_FIELD_NUMBER: builtins.int
    H_FIELD_NUMBER: builtins.int
    I_FIELD_NUMBER: builtins.int
    J_FIELD_NUMBER: builtins.int
    K_FIELD_NUMBER: builtins.int
    a: builtins.str
    """Ending with " """
    b: builtins.str
    """Ending with "" """
    c: builtins.str
    """Ending with \"\"\" """
    d: builtins.str
    """Ending with \\ """
    e: builtins.str
    """Containing bad escape: \\x"""
    f: builtins.str
    """Containing \"\"\"" quadruple"""
    g: builtins.str
    """Containing \"\"\""" quintuple"""
    h: builtins.str
    """Containing \"\"\"\"\"\" sextuple"""
    i: builtins.str
    """\"\"\" Multiple \"\"\" triples \"\"\" """
    j: builtins.str
    """"quotes" can be a problem in comments.
    \"\"\"Triple quotes\"\"\" just as well
    """
    k: builtins.str
    """\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"
    "                                              "
    " Super Duper comments with surrounding edges! "
    "                                              "
    "            Pay attention to me!!!!           "
    "                                              "
    \"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"
    """
    def __init__(
        self,
        *,
        a: builtins.str = ...,
        b: builtins.str = ...,
        c: builtins.str = ...,
        d: builtins.str = ...,
        e: builtins.str = ...,
        f: builtins.str = ...,
        g: builtins.str = ...,
        h: builtins.str = ...,
        i: builtins.str = ...,
        j: builtins.str = ...,
        k: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["a", b"a", "b", b"b", "c", b"c", "d", b"d", "e", b"e", "f", b"f", "g", b"g", "h", b"h", "i", b"i", "j", b"j", "k", b"k"]) -> None: ...

global___Test: typing_extensions.TypeAlias = Test
