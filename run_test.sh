#!/bin/bash -ex

(
    # Create virtualenv + Install requirements for mypy-protobuf
    python -m virtualenv env
    source env/bin/activate
    python -m pip install -r requirements.txt

    # Generate protos
    protoc --python_out=. --mypy_out=. --plugin=protoc-gen-mypy=python/protoc-gen-mypy --proto_path=proto/ `find proto/test -name "*.proto"`

    # Run unit tests
    py.test
)

(
    # Uncomment these to run on mac
    #eval "$(pyenv init -)"
    #pyenv shell 3.5.5

    : ${PY:=2.7}

    # Create virtualenv
    python3 -m virtualenv mypy_env
    source mypy_env/bin/activate
    python3 -m pip install setuptools
    python3 -m pip install git+git://github.com/python/mypy.git@9bfd5ee9a60a500d05479f0b61b61000500bb6dc

    # Run mypy
    mypy --python-version=$PY python/protoc-gen-mypy test/

    diff <(mypy --python-version=$PY python/protoc-gen-mypy test_negative/) test_negative/output.expected.$PY
)
