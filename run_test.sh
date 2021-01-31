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

    PROTOC_ARGS="--proto_path=proto/ --experimental_allow_proto3_optional"
    $PROTOC $PROTOC_ARGS --mypy_out=generated `find proto -name "*.proto"`
    $PROTOC $PROTOC_ARGS --python_out=generated `find proto/testproto -name "*.proto"`
    if [[ $PY_VER_MYPY_PROTOBUF =~ ^3.* ]]; then
        GRPC_PROTOS=$(find proto/testproto/grpc -name "*.proto")
        $PROTOC $PROTOC_ARGS --mypy_grpc_out=generated $GRPC_PROTOS
        python -m grpc_tools.protoc $PROTOC_ARGS --grpc_python_out=generated $GRPC_PROTOS
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
        python3 --version
        python3 -m pip --version
        python3 -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python3 -m pip install setuptools
        python3 -m pip install mypy==0.800
        python3 -m pip install -r requirements.txt
    fi

    # Run mypy
    mypy --version
    # --python-version=2.7 chokes on the generated grpc files - so split them out here
    FILES27="python/mypy_protobuf.py $(find test -name "*.py" | grep -v grpc)  $(find generated -name "*.pyi" | grep -v grpc)"
    FILES35="python/mypy_protobuf.py test/ generated/"
    if [ $PY_VER_MYPY_TARGET = "2.7" ]; then
        FILES=$FILES27
    else
        FILES=$FILES35
    fi
    mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET --pretty --show-error-codes $FILES

    # run mypy on negative-tests (expected failures)
    # --python-version=2.7 chokes on the generated grpc files - so split them out here
    NEGATIVE_FILES_27="test_negative/negative.py test_negative/negative_2.7.py $FILES27"
    NEGATIVE_FILES_35="test_negative/negative.py test_negative/negative_3.5.py $FILES35"
    if [ $PY_VER_MYPY_TARGET = "2.7" ]; then
        NEGATIVE_FILES=$NEGATIVE_FILES_27
    else
        NEGATIVE_FILES=$NEGATIVE_FILES_35
    fi

    if ! diff <(mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET $NEGATIVE_FILES) test_negative/output.expected.$PY_VER_MYPY_TARGET; then
        echo -e "${RED}test_negative/output.expected.$PY_VER_MYPY_TARGET didnt match. Copying over for you. Now rerun${NC}"

        # Copy over all the py targets for convenience for the developer - so they don't have to run it many times
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=2.7 $NEGATIVE_FILES_27 > test_negative/output.expected.2.7 || true
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=3.5 $NEGATIVE_FILES_35 > test_negative/output.expected.3.5 || true
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
    if [[ $PY_VER_UNIT_TESTS =~ ^2.* ]]; then IGNORE="--ignore=test/test_grpc_usage.py"; else IGNORE=""; fi
    PYTHONPATH=generated py.test --ignore=generated $IGNORE -v
)
