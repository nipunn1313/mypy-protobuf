#!/bin/bash -ex

RED="\033[0;31m"
NC='\033[0m'
PROTOC=${PROTOC:=protoc}

PY_VER_MYPY_PROTOBUF=${PY_VER_MYPY_PROTOBUF:=3.8.6}
PY_VER_MYPY=${PY_VER_MYPY:=3.8.6}
PY_VER_MYPY_TARGET=${PY_VER_MYPY_TARGET:=3.5}
PY_VER_UNIT_TESTS=${PY_VER_UNIT_TESTS:=3.8.6}

# Clean out generated/ directory - except for .generated / __init__.py
find generated -type f -not \( -name "*.expected" -or -name "__init__.py" \) -delete

(
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_MYPY_PROTOBUF
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`

    VENV=venv_$PY_VERSION

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
    expected="libprotoc 3.14.0"
    if [[ $($PROTOC --version) != $expected ]]; then
        echo -e "${RED}For tests - must install protoc version ${expected} ${NC}"
        exit 1
    fi
    $PROTOC --mypy_out=generated --proto_path=proto/ --experimental_allow_proto3_optional `find proto/ -name "*.proto"`
    $PROTOC --python_out=generated --proto_path=proto/ --experimental_allow_proto3_optional `find proto/testproto -name "*.proto"`
    if [[ $PY_VER_MYPY_TARGET = 3.5 ]]; then
        $PROTOC --mypy_grpc_out=generated --proto_path=proto/ --experimental_allow_proto3_optional `find proto/testproto/grpc -name "*.proto"`
        if [[ "$PY_VER_MYPY_PROTOBUF" =~ ^3.* ]]; then
            python -m grpc_tools.protoc --grpc_python_out=generated --proto_path=proto/ --experimental_allow_proto3_optional  `find proto/testproto/grpc -name "*.proto"`
        fi
    fi
)

(
    # Run mypy
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_MYPY
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
    VENV=venv_$PY_VERSION

    # Create virtualenv
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        rm -rf $VENV
        python3 --version
        python3 -m pip --version
        python3 -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python3 -m pip install setuptools
        python3 -m pip install --ignore-requires-python grpc-stubs
        python3 -m pip install git+https://github.com/python/mypy.git@985a20d87eb3a516ff4457041a77026b4c6bd784
    fi

    # Run mypy
    mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET --pretty --show-error-codes python/mypy_protobuf.py test/ generated/
    if ! diff <(mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET python/mypy_protobuf.py test_negative/negative.py test_negative/negative_$PY_VER_MYPY_TARGET.py generated/) test_negative/output.expected.$PY_VER_MYPY_TARGET; then
        echo -e "${RED}test_negative/output.expected.$PY_VER_MYPY_TARGET didnt match. Copying over for you. Now rerun${NC}"
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET python/mypy_protobuf.py test_negative/negative.py test_negative/negative_$PY_VER_MYPY_TARGET.py generated/ > test_negative/output.expected.$PY_VER_MYPY_TARGET || true
        exit 1
    fi
)

(
    # Run unit tests. These tests generate .expected files
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_UNIT_TESTS
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
    VENV=venv_$PY_VERSION

    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    python -m pip install -r requirements.txt

    python --version
    py.test --version
    if [[ "$PY_VER_UNIT_TESTS" =~ ^3.* ]] && [[ "$PY_VER_MYPY_PROTOBUF" =~ ^3.* ]]; then
        PYTHONPATH=generated py.test -svvv --ignore=generated
    else
        PYTHONPATH=generated py.test -svvv --ignore=generated --ignore-glob=test/*grpc*
    fi
)
