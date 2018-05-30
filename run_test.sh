#!/bin/bash -ex

# Install requirements
python -m pip install -r requirements.txt

# Generate protos
protoc --mypy_out=test/output/ --plugin=protoc-gen-mypy=python/protoc-gen-mypy --proto_path=test/proto/ `find test/proto -name "*.proto"`

# Run unit tests
(cd test ; py.test)

# Run mypy
mypy --python-version=2.7 python/protoc-gen-mypy test/
