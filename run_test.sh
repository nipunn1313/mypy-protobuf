#!/bin/bash -ex

(
    # Create virtualenv + Install requirements for mypy-protobuf
    python -m pip install --user virtualenv
    python -m virtualenv env
    source env/bin/activate
    python -m pip install -r requirements.txt

    # Generate protos
    protoc --python_out=test/output/ --mypy_out=test/output/ --plugin=protoc-gen-mypy=python/protoc-gen-mypy --proto_path=test/proto/ `find test/proto -name "*.proto"`

    # Run unit tests
    cd test
    py.test
)

(
    # Uncomment these to run on mac
    #eval "$(pyenv init -)"
    #pyenv shell 3.5.5

    # Create virtualenv
    python3 -m pip install --user virtualenv
    python3 -m virtualenv mypy_env
    source mypy_env/bin/activate
    python3 -m pip install -U setuptools
    python3 -m pip install -U git+git://github.com/python/mypy.git

    # Run mypy
    mypy --python-version=$PY python/protoc-gen-mypy test/
)
