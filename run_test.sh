#!/bin/bash -ex

RED="\033[0;31m"
NC='\033[0m'

PY_VER_MYPY_PROTOBUF=${PY_VER_MYPY_PROTOBUF:=3.11.4}
PY_VER_MYPY_PROTOBUF_SHORT=$(echo "$PY_VER_MYPY_PROTOBUF" | cut -d. -f1-2)
PY_VER_MYPY=${PY_VER_MYPY:=3.8.17}
PY_VER_UNIT_TESTS="${PY_VER_UNIT_TESTS:=3.8.17 3.13.9 3.14.0}"



if [ -e "$CUSTOM_TYPESHED_DIR" ]; then
    export MYPYPATH=$CUSTOM_TYPESHED_DIR/stubs/protobuf
    export CUSTOM_TYPESHED_DIR_ARG="--custom-typeshed-dir=$CUSTOM_TYPESHED_DIR"
else
    # mypy does not emit deprecation warnings for typeshed stubs. Setting an empty custom-typeshed-dir was causing the current directory to be considered a typeshed dir, and hiding deprecation warnings.
    export CUSTOM_TYPESHED_DIR_ARG=""
fi

# Install protoc
PYTHON_PROTOBUF_VERSION=$(grep "^protobuf==" test_requirements.txt | cut -f3 -d=)
PROTOBUF_VERSION=$(echo "$PYTHON_PROTOBUF_VERSION" | cut -f2-3 -d.)
PROTOC_DIR="protoc_$PROTOBUF_VERSION"
if [[ -z $SKIP_CLEAN ]] || [[ ! -e $PROTOC_DIR ]]; then
    if uname -a | grep Darwin; then
        # brew install coreutils wget
        PLAT=osx
    else
        PLAT=linux
    fi

    PROTOC_FILENAME="protoc-${PROTOBUF_VERSION}-${PLAT}-x86_64.zip"
    PROTOC_URL="https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOBUF_VERSION}/$PROTOC_FILENAME"

    rm -rf "$PROTOC_DIR"
    wget "$PROTOC_URL" -P "$PROTOC_DIR"
    mkdir -p "$PROTOC_DIR/protoc_install"
    unzip "$PROTOC_DIR/$PROTOC_FILENAME" -d "$PROTOC_DIR/protoc_install"
fi
PROTOC="$PROTOC_DIR/protoc_install/bin/protoc"
if [[ $($PROTOC --version) != "libprotoc $PROTOBUF_VERSION" ]]; then
    echo -e "${RED}Wrong protoc installed?"
    exit 1
fi

PROTOC_ARGS=( --proto_path=proto/ --proto_path="$PROTOC_DIR/protoc_install/include" --experimental_allow_proto3_optional )

# Create mypy venv
MYPY_VENV=venv_$PY_VER_MYPY
(
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    pyenv shell "$PY_VER_MYPY"

    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_VENV ]]; then
        python3 --version
        python3 -m pip --version
        python -m pip install virtualenv
        python3 -m virtualenv "$MYPY_VENV"
        "$MYPY_VENV"/bin/python3 -m pip install -r mypy_requirements.txt
    fi
    "$MYPY_VENV"/bin/mypy --version
)

# Create unit tests venvs
for PY_VER in $PY_VER_UNIT_TESTS; do
    (
        UNIT_TESTS_VENV=venv_$PY_VER
        eval "$(pyenv init --path)"
        eval "$(pyenv init -)"
        pyenv shell "$PY_VER"

        if [[ -z $SKIP_CLEAN ]] || [[ ! -e $UNIT_TESTS_VENV ]]; then
            python -m pip install virtualenv
            python -m virtualenv "$UNIT_TESTS_VENV"
            "$UNIT_TESTS_VENV"/bin/python -m pip install -r test_requirements.txt
        fi
        "$UNIT_TESTS_VENV"/bin/py.test --version
    )
done

# Create mypy-protobuf venv
MYPY_PROTOBUF_VENV=venv_$PY_VER_MYPY_PROTOBUF
(
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    pyenv shell "$PY_VER_MYPY_PROTOBUF"

    # Create virtualenv + Install requirements for mypy-protobuf
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_PROTOBUF_VENV ]]; then
        python -m pip install virtualenv
        python -m virtualenv "$MYPY_PROTOBUF_VENV"
        "$MYPY_PROTOBUF_VENV"/bin/python -m pip install -e .
    fi
)

# Run mypy-protobuf
(
    source "$MYPY_PROTOBUF_VENV"/bin/activate

    # Confirm version number
    test "$(protoc-gen-mypy -V)" = "mypy-protobuf 3.7.0"
    test "$(protoc-gen-mypy --version)" = "mypy-protobuf 3.7.0"
    test "$(protoc-gen-mypy_grpc -V)" = "mypy-protobuf 3.7.0"
    test "$(protoc-gen-mypy_grpc --version)" = "mypy-protobuf 3.7.0"

    # Run mypy on mypy-protobuf internal code for developers to catch issues
    FILES="mypy_protobuf/main.py"
    "$MYPY_VENV/bin/mypy" ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --python-executable="$MYPY_PROTOBUF_VENV/bin/python3" --python-version="$PY_VER_MYPY_PROTOBUF_SHORT" $FILES

    # Generate protos
    python --version
    $PROTOC --version

    # CI Check to make sure generated files are committed
    SHA_BEFORE=$(find test/generated -name "*.pyi" -print0 | xargs -0 sha1sum)
    # Clean out generated/ directory - except for __init__.py
    find test/generated -type f -not -name "__init__.py" -delete

    # Compile protoc -> python
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --python_out=test/generated

    # Compile protoc -> mypy using mypy_protobuf
    # Prereq - create the mypy.proto python proto
    find proto/mypy_protobuf -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --python_out=.
    find proto/mypy_protobuf -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=.

    # Sanity check that our flags work
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=quiet:test/generated
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=readable_stubs:test/generated
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=relax_strict_optional_primitives:test/generated
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=use_default_deprecation_warnings:test/generated
    # Overwrite w/ run with mypy-protobuf without flags
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=test/generated

    # Generate grpc protos
    find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_grpc_out=test/generated

    if [[ -n $VALIDATE ]] && ! diff <(echo "$SHA_BEFORE") <(find test/generated -name "*.pyi" -print0 | xargs -0 sha1sum); then
        echo -e "${RED}Some .pyi files did not match. Please commit those files${NC}"
        exit 1
    fi
)

for PY_VER in $PY_VER_UNIT_TESTS; do
    UNIT_TESTS_VENV=venv_$PY_VER
    PY_VER_MYPY_TARGET=$(echo "$PY_VER" | cut -d. -f1-2)

    # Generate GRPC protos for mypy / tests
    (
        source "$UNIT_TESTS_VENV"/bin/activate
        find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 python -m grpc_tools.protoc "${PROTOC_ARGS[@]}" --grpc_python_out=test/generated
    )

    # Run mypy on unit tests / generated output
    (
        source "$MYPY_VENV"/bin/activate
        export MYPYPATH=$MYPYPATH:test/generated

        # Run mypy
        MODULES=( -m test.test_generated_mypy -m test.test_grpc_usage -m test.test_grpc_async_usage )
        mypy ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${MODULES[@]}"

        # Run stubtest. Stubtest does not work with python impl - only cpp impl
        pip install -r test_requirements.txt
        API_IMPL="$(python3 -c "import google.protobuf.internal.api_implementation as a ; print(a.Type())")"
        if [[ $API_IMPL != "python" ]]; then
            PYTHONPATH=test/generated python3 -m mypy.stubtest ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --allowlist stubtest_allowlist.txt testproto
        fi

        # run mypy on negative-tests (expected mypy failures)
        NEGATIVE_MODULES=( -m test_negative.negative "${MODULES[@]}" )

        MYPY_OUTPUT=$(mktemp -d)
        call_mypy() {
            # Write output to file. Make variant w/ omitted line numbers for easy diffing / CR
            PY_VER_MYPY_TARGET=$(echo "$1" | cut -d. -f1-2)
            export MYPYPATH=$MYPYPATH:test/generated
            # Use --no-incremental to avoid caching issues: https://github.com/python/mypy/issues/16363
            mypy ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --python-executable="venv_$1/bin/python" --no-incremental --python-version="$PY_VER_MYPY_TARGET" "${@: 2}" > "$MYPY_OUTPUT/mypy_output" || true
            cut -d: -f1,3- "$MYPY_OUTPUT/mypy_output" > "$MYPY_OUTPUT/mypy_output.omit_linenos"
        }

        call_mypy "$PY_VER" "${NEGATIVE_MODULES[@]}"
        if ! diff "$MYPY_OUTPUT/mypy_output" "test_negative/output.expected.$PY_VER_MYPY_TARGET" || ! diff "$MYPY_OUTPUT/mypy_output.omit_linenos" "test_negative/output.expected.$PY_VER_MYPY_TARGET.omit_linenos"; then
            echo -e "${RED}test_negative/output.expected.$PY_VER_MYPY_TARGET didnt match. Copying over for you. Now rerun${NC}"

            # Copy over all the mypy results for the developer.
            call_mypy "$PY_VER" "${NEGATIVE_MODULES[@]}"
            cp "$MYPY_OUTPUT/mypy_output" "test_negative/output.expected.$PY_VER_MYPY_TARGET"
            cp "$MYPY_OUTPUT/mypy_output.omit_linenos" "test_negative/output.expected.$PY_VER_MYPY_TARGET.omit_linenos"
            exit 1
        fi
    )

    (
        # Run unit tests.
        source "$UNIT_TESTS_VENV"/bin/activate
        PYTHONPATH=test/generated py.test --ignore=test/generated -v
    )
done
