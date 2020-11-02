#!/bin/bash -ex

PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
VENV=venv_$PY_VERSION
MYPY_VENV=venv_mypy

RED="\033[0;31m"
NC='\033[0m'
PROTOC=${PROTOC:=protoc}

(
    # Create virtualenv + Install requirements for mypy-protobuf
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    python -m pip install python/ -r requirements.txt

    # Generate protos
    $PROTOC --version
    expected="libprotoc 3.13.0"
    if [[ $($PROTOC --version) != $expected ]]; then
        echo -e "${RED}For tests - must install protoc version ${expected} ${NC}"
        exit 1
    fi
    $PROTOC --mypy_out=generated --proto_path=proto/ `find proto/ -name "*.proto"`
    $PROTOC --python_out=generated --proto_path=proto/ `find proto/testproto -name "*.proto"`
)

(
    # Run mypy (always under python3)

    # Create virtualenv
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_VENV ]]; then
        python3 --version
        python3 -m pip --version
        python3 -m virtualenv $MYPY_VENV
    fi
    source $MYPY_VENV/bin/activate
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_VENV ]]; then
        python3 -m pip install setuptools
        python3 -m pip install git+https://github.com/python/mypy.git@985a20d87eb3a516ff4457041a77026b4c6bd784
    fi

    # Run mypy
    for PY in 2.7 3.5; do
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY --pretty --show-error-codes python/mypy_protobuf.py test/ generated/
        if ! diff <(mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY python/mypy_protobuf.py test_negative/ generated/) test_negative/output.expected.$PY; then
            echo -e "${RED}test_negative/output.expected.$PY didnt match. Copying over for you. Now rerun${NC}"
            for PY in 2.7 3.5; do
                mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY python/mypy_protobuf.py test_negative/ generated/ > test_negative/output.expected.$PY || true
            done
            exit 1
        fi
    done
)

(
    # Run unit tests. These tests generate .expected files
    source $VENV/bin/activate
    python --version
    py.test --version
    PYTHONPATH=generated py.test --ignore=generated
)
