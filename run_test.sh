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
)

(
    # Run mypy
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_MYPY
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
    VENV=venv_$PY_VERSION

    # Create virtualenv
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python3 --version
        python3 -m pip --version
        python3 -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python3 -m pip install setuptools
        python3 -m pip install mypy==0.800
    fi

    # Run mypy
    mypy --version
    mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET --pretty --show-error-codes python/mypy_protobuf.py test/ generated/
    if ! diff <(mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET python/mypy_protobuf.py test_negative/ generated/) test_negative/output.expected.$PY_VER_MYPY_TARGET.txt; then
        echo -e "${RED}test_negative/output.expected.$PY_VER_MYPY_TARGET.txt didnt match. Copying over for you. Now rerun${NC}"

        # Copy over all the py targets for convenience for the developer - so they don't have to run it many times
        for PY in 2.7 3.5; do
            mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY python/mypy_protobuf.py test_negative/ generated/ > test_negative/output.expected.$PY.txt || true
        done
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
    PYTHONPATH=generated py.test --ignore=generated
)
