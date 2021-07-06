#!/bin/bash -ex

RED="\033[0;31m"
NC='\033[0m'
PROTOC=${PROTOC:=protoc}

PY_VER_MYPY_PROTOBUF=${PY_VER_MYPY_PROTOBUF:=3.9.0}
PY_VER_MYPY=${PY_VER_MYPY:=3.8.6}
PY_VER_MYPY_TARGET=${PY_VER_MYPY_TARGET:=3.8}
PY_VER_UNIT_TESTS=${PY_VER_UNIT_TESTS:=3.8.6}

# Clean out generated/ directory - except for .generated / __init__.py
find test/generated -type f -not \( -name "*.expected" -or -name "__init__.py" \) -delete

(
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_MYPY_PROTOBUF
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
    VENV=venv_$PY_VERSION

    # Create virtualenv + Install requirements for mypy-protobuf
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python -m pip install virtualenv
        python -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    if [[ -z $SKIP_CLEAN ]]; then
        python -m pip install -r requirements.txt
        python -m pip install -e .
    fi

    # Generate protos
    python --version
    $PROTOC --version
    expected="libprotoc 3.14.0"
    if [[ $($PROTOC --version) != $expected ]]; then
        echo -e "${RED}For tests - must install protoc version ${expected} ${NC}"
        exit 1
    fi

    PROTOC_ARGS="--proto_path=proto/ --experimental_allow_proto3_optional"
    # Compile protoc -> python
    $PROTOC $PROTOC_ARGS --python_out=test/generated `find proto -name "*.proto"`

    # Compile protoc -> mypy using mypy_protobuf
    # Prereq - create the mypy.proto python proto
    $PROTOC $PROTOC_ARGS --python_out=. `find proto/mypy_protobuf -name "*.proto"`
    $PROTOC $PROTOC_ARGS --mypy_out=. `find proto/mypy_protobuf -name "*.proto"`

    # Sanity check that our flags work
    $PROTOC $PROTOC_ARGS --mypy_out=quiet:test/generated `find proto -name "*.proto"`
    $PROTOC $PROTOC_ARGS --mypy_out=readable_stubs:test/generated `find proto -name "*.proto"`
    $PROTOC $PROTOC_ARGS --mypy_out=relax_strict_optional_primitives:test/generated `find proto -name "*.proto"`
    # Overwrite w/ run with mypy-protobuf without flags
    $PROTOC $PROTOC_ARGS --mypy_out=test/generated `find proto -name "*.proto"`

    # Compile GRPC
    GRPC_PROTOS=$(find proto/testproto/grpc -name "*.proto")
    $PROTOC $PROTOC_ARGS --mypy_grpc_out=test/generated $GRPC_PROTOS
    python -m grpc_tools.protoc $PROTOC_ARGS --grpc_python_out=test/generated $GRPC_PROTOS
)

(
    # Run mypy
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_MYPY
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
    VENV=venv_$PY_VERSION

    # Create virtualenv
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python3 --version
        python3 -m pip --version
        python -m pip install virtualenv
        python3 -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    if [[ -z $SKIP_CLEAN ]]; then
        python3 -m pip install setuptools
        python3 -m pip install mypy==0.800
        python3 -m pip install -r requirements.txt
    fi

    # Run mypy
    mypy --version
    # --python-version=2.7 chokes on the generated grpc files - so split them out here
    FILES27="$(ls test/*.py | grep -v grpc)  $(find test/generated -name "*.pyi" | grep -v grpc)"
    FILES38="mypy_protobuf/main.py test/"
    if [ $PY_VER_MYPY_TARGET = "2.7" ]; then
        FILES=$FILES27
    else
        FILES=$FILES38
    fi
    mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET --pretty --show-error-codes $FILES

    # run mypy on negative-tests (expected mypy failures)
    # --python-version=2.7 chokes on the generated grpc files - so split them out here
    NEGATIVE_FILES_27="test_negative/negative.py test_negative/negative_2.7.py $FILES27"
    NEGATIVE_FILES_38="test_negative/negative.py test_negative/negative_3.8.py $FILES38"
    if [ $PY_VER_MYPY_TARGET = "2.7" ]; then
        NEGATIVE_FILES=$NEGATIVE_FILES_27
    else
        NEGATIVE_FILES=$NEGATIVE_FILES_38
    fi

    if ! diff <(mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=$PY_VER_MYPY_TARGET $NEGATIVE_FILES) test_negative/output.expected.$PY_VER_MYPY_TARGET; then
        echo -e "${RED}test_negative/output.expected.$PY_VER_MYPY_TARGET didnt match. Copying over for you. Now rerun${NC}"

        # Copy over all the py targets for convenience for the developer - so they don't have to run it many times
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=2.7 $NEGATIVE_FILES_27 > test_negative/output.expected.2.7 || true
        mypy --custom-typeshed-dir=$CUSTOM_TYPESHED_DIR --python-version=3.8 $NEGATIVE_FILES_38 > test_negative/output.expected.3.8 || true
        exit 1
    fi
)

(
    # Run unit tests. These tests generate .expected files
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    pyenv shell $PY_VER_UNIT_TESTS
    PY_VERSION=`python -c 'import sys; print(sys.version.split()[0])'`
    VENV=venv_$PY_VERSION

    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $VENV ]]; then
        python -m pip install virtualenv
        python -m virtualenv $VENV
    fi
    source $VENV/bin/activate
    python -m pip install -r requirements.txt

    python --version
    py.test --version
    if [[ $PY_VER_UNIT_TESTS =~ ^2.* ]]; then IGNORE="--ignore=test/test_grpc_usage.py"; else IGNORE=""; fi
    PYTHONPATH=test/generated py.test --ignore=test/generated $IGNORE -v
)
