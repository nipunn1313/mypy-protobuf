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
    # Git rev from 08/18/2018. Prefer a tag (eg @v0.620) once a lter one is released
    python3 -m pip install git+git://github.com/python/mypy.git@402d734c4b8ceffdc04478eb49fc196dd2a3a785

    # Run mypy
    mypy --python-version=$PY python/protoc-gen-mypy test/

    diff <(mypy --python-version=$PY python/protoc-gen-mypy test_negative/) test_negative/output.expected.$PY
)
