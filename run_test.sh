#!/bin/bash -ex

(
    # Create virtualenv + Install requirements for mypy-protobuf
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e env ]]; then
        python -m virtualenv env
    fi
    source env/bin/activate
    python -m pip install -r requirements.txt

    # Generate protos
    protoc --version
    protoc --python_out=. --mypy_out=. --plugin=protoc-gen-mypy=python/protoc-gen-mypy --proto_path=proto/ `find proto/test -name "*.proto"`
)

(
    # Run mypy

    # Uncomment these to run on mac
    # eval "$(pyenv init -)"
    # pyenv shell 3.5.5

    # Create virtualenv
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e mypy_env ]]; then
        python3 -m virtualenv mypy_env
    fi
    source mypy_env/bin/activate
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e mypy_env ]]; then
        python3 -m pip install setuptools
        python3 -m pip install git+https://github.com/python/mypy.git@69a0560b471e8682cbed782997d140694c841cc2
    fi

    # Run mypy
    for PY in 2.7 3.5; do
        mypy --python-version=$PY python/protoc-gen-mypy test/
        if ! diff <(mypy --python-version=$PY python/protoc-gen-mypy test_negative/) test_negative/output.expected.$PY; then
            echo "test_negative/output.expected.$PY didnt match. Copying over for you. Now rerun"
            for PY in 2.7 3.5; do
                mypy --python-version=$PY python/protoc-gen-mypy test_negative/ > test_negative/output.expected.$PY || true
            done
            exit 1
        fi
    done
)

(
    # Run unit tests. These tests generate .expected files
    source env/bin/activate
    python --version
    py.test --version
    py.test
)
