import glob
import os

from test.output.test_pb2 import Simple1

def test_generate_mypy_matches():
    # type: () -> None
    proto_files = glob.glob('test/proto/**.proto')
    assert len(proto_files) == 2  # Just a sanity check that all the files show up

    failures = []
    for fn in proto_files:
        fn_split = fn.split(os.sep)  # Eg. [test, proto, test.proto]
        fn_split[1] = 'output'  # Eg [test, output, test.proto]
        assert fn_split[-1].endswith('.proto')
        fn_split[-1] = fn_split[-1][:-len('.proto')] + '_pb2.pyi'  # Eg [test, output, test_pb2.proto]

        output = os.path.join(*fn_split)

        fn_split[-1] += '.expected'  # Eg [test, output, test_pb2.proto.expected]

        expected = os.path.join(*fn_split)

        assert os.path.exists(output)
        assert os.path.exists(expected)

        output_contents = open(output).read()
        expected_contents = open(expected).read()

        if output_contents != expected_contents:
            open(expected, "w").write(output_contents)
            failures.append(("%s doesn't match %s. This test will copy it over." % (output, expected)))

    if failures:
        raise Exception(str(failures))

def test_func():
    s = Simple1()
    s.a_string = "Hello"

    s2 = Simple1.FromString(s.SerializeToString())
    assert s2.a_string == "Hello"

    s3 = Simple1()
    s3.ParseFromString(s.SerializeToString())
    assert s3.a_string == "Hello"

    s4 = Simple1()
    s4.CopyFrom(s)
    assert s4.a_string == "Hello"
