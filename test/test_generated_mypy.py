import glob
import os

def test_generate_mypy_matches():
    # type: () -> None
    proto_files = glob.glob('proto/**.proto')
    assert len(proto_files) == 2  # Just a sanity check that all the files show up

    for fn in proto_files:
        fn_split = fn.split(os.sep)  # Eg. [proto, test.proto]
        fn_split[0] = 'output'  # Eg [output, test.proto]
        assert fn_split[-1].endswith('.proto')
        fn_split[-1] = fn_split[-1][:-len('.proto')] + '_pb2.pyi'  # Eg [output, test_pb2.proto]

        output = os.path.join(*fn_split)

        fn_split[-1] += '.expected'  # Eg [output, test_pb2.proto.expected]

        expected = os.path.join(*fn_split)

        assert os.path.exists(output)
        assert os.path.exists(expected)

        output_contents = open(output).read()
        expected_contents = open(expected).read()
        assert output_contents == expected_contents
