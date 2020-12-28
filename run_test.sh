#!/bin/bash -ex

PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
VENV=venv_$PY_VERSION
MYPY_VENV=venv_mypy

RED="\033[0;31m"
NC='\033[0m'
PROTOC=${PROTOC:=protoc}

# Clean out generated/ directory - except for .generated / __init__.py
find generated -type f -not \( -name "*.expected" -or -name "__init__.py" \) -delete

(
    # Create virtualenv + Install requirements for mypy-protobuf
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        rm -rf $VENV
        python -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    python -m pip install python/ -r requirements.txt

    # Generate protos
    python --version
    $PROTOC --version
    expected="libprotoc 3.13.0"
    if [[ $($PROTOC --version) != $expected ]]; then
        echo -e "${RED}For tests - must install protoc version ${expected} ${NC}"
        exit 1
    fi
    $PROTOC --mypy_out=generated --proto_path=proto/ --experimental_allow_proto3_optional `find proto/ -name "*.proto"`
    $PROTOC --python_out=generated --proto_path=proto/ --experimental_allow_proto3_optional `find proto/testproto -name "*.proto"`

    CAN_GENERATE_GRPC_OUTPUT=`python -c 'import sys;print(sys.version_info.major>=3 and sys.version_info.minor>=6)'`
    if [ $CAN_GENERATE_GRPC_OUTPUT = 'True' ]; then
        $PROTOC --mypy_grpc_out=generated --proto_path=proto/ --experimental_allow_proto3_optional `find proto/testproto/grpc -name "*.proto"`
    fi
)

(
    # Run mypy (always under python3)

    # Create virtualenv
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_VENV ]]; then
        rm -rf $MYPY_VENV
        python3 --version
        python3 -m pip --version
        python3 -m virtualenv $MYPY_VENV
    fi
    source $MYPY_VENV/bin/activate
    CAN_TEST_GRPC_OUTPUT=`python -c 'import sys;print(sys.version_info.major>=3 and sys.version_info.minor>=6)'`
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_VENV ]]; then
        python3 -m pip install setuptools
        if [ $CAN_TEST_GRPC_OUTPUT = 'True' ]; then
            python3 -m pip install grpc-stubs
        fi
        python3 -m pip install git+https://github.com/python/mypy.git@985a20d87eb3a516ff4457041a77026b4c6bd784
    fi

    # preparing isolated folder for testing mypy per python version
    rm -rf generated_3.5
    cp -R generated generated_3.5

    rm -rf generated_2.7
    cp -R generated generated_2.7
    find generated_2.7 -name '*grpc.pyi' -exec rm {} \;
    find generated_2.7 -name '*grpc.pyi.expected' -exec rm {} \;

    # Run mypy
    for PY in 2.7 3.5; do
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY --pretty --show-error-codes python/mypy_protobuf.py test/ generated_$PY/
        if ! diff <(mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY python/mypy_protobuf.py test_negative/ generated_$PY/) test_negative/output.expected.$PY; then
            echo -e "${RED}test_negative/output.expected.$PY didnt match. Copying over for you. Now rerun${NC}"
            for PY in 2.7 3.5; do
                mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY python/mypy_protobuf.py test_negative/ generated_$PY/ > test_negative/output.expected.$PY || true
            done
            exit 1
        fi
    done

    rm -rf generated_3.5
    rm -rf generated_2.7
)

(
    # Run unit tests. These tests generate .expected files
    source $VENV/bin/activate
    python --version
    py.test --version
    PYTHONPATH=generated py.test --ignore=generated
)
