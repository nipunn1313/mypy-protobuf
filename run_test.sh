#!/bin/bash -ex

(
    # Create virtualenv + Install requirements for mypy-protobuf
    python -m virtualenv env
    source env/bin/activate
    python -m pip install -r requirements.txt

    # Generate protos
    protoc --version
    protoc --python_out=. --mypy_out=. --plugin=protoc-gen-mypy=python/protoc-gen-mypy --proto_path=proto/ `find proto/test -name "*.proto"`

    # Run unit tests
    python --version
    py.test --version
    py.test
)

(
    # Uncomment these to run on mac
    # eval "$(pyenv init -)"
    # pyenv shell 3.5.5

    : ${PY:=2.7}

    # Create virtualenv
    python3 -m virtualenv mypy_env
    source mypy_env/bin/activate
    python3 -m pip install setuptools
    python3 -m pip install git+https://github.com/python/mypy.git@v0.641

    # Run mypy
    mypy --python-version=$PY python/protoc-gen-mypy test/

    diff <(mypy --python-version=$PY python/protoc-gen-mypy test_negative/) test_negative/output.expected.$PY
)
