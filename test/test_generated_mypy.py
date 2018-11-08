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

from test.proto.test_pb2 import Simple1

def test_generate_mypy_matches():
    # type: () -> None
    proto_files = (
        glob.glob('proto/test/proto/*.proto') +
        glob.glob('proto/test/proto/*/*.proto')
    )
    assert len(proto_files) == 7  # Just a sanity check that all the files show up

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
