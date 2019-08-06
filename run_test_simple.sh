#!/usr/bin/env bash
# Different from `run_test.sh`, this script does not create virtualenvs,
# therefore it should be executed after environment has been completed prepared and activated

set -e

(
    echo "--- Generate protos ---"
    protoc --python_out=. --mypy_out=. \
        --plugin=protoc-gen-mypy=python/protoc-gen-mypy \
        --proto_path=proto/ `find proto/test -name "*.proto"`
)

(
    echo
    echo "--- Run mypy ---"
    # Run mypy (always under python3)
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
    echo
    echo "--- Run pytest ---"
    py.test --ignore-glob '*_pb2.py'
)
