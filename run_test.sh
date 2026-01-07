#!/bin/bash -ex

RED="\033[0;31m"
NC='\033[0m'

PY_VER_MYPY_PROTOBUF=${PY_VER_MYPY_PROTOBUF:=3.12.12}
PY_VER_MYPY_PROTOBUF_SHORT=$(echo "$PY_VER_MYPY_PROTOBUF" | cut -d. -f1-2)
PY_VER_MYPY=${PY_VER_MYPY:=3.12.12}
PY_VER_UNIT_TESTS="${PY_VER_UNIT_TESTS:=3.9.17 3.10.12 3.11.4 3.12.12 3.13.9 3.14.0}"
PYTHON_PROTOBUF_VERSION=${PYTHON_PROTOBUF_VERSION:=6.32.1}
TEST_THIRD_PARTY=${TEST_THIRD_PARTY:=0}
READABLE_STUBS=${READABLE_STUBS:=0}

# Confirm UV installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}uv could not be found, please install uv (https://docs.astral.sh/uv/getting-started/installation/)${NC}"
    exit 1
fi


if [ -e "$CUSTOM_TYPESHED_DIR" ]; then
    export MYPYPATH=$CUSTOM_TYPESHED_DIR/stubs/protobuf
    export CUSTOM_TYPESHED_DIR_ARG="--custom-typeshed-dir=$CUSTOM_TYPESHED_DIR"
else
    # mypy does not emit deprecation warnings for typeshed stubs. Setting an empty custom-typeshed-dir was causing the current directory to be considered a typeshed dir, and hiding deprecation warnings.
    export CUSTOM_TYPESHED_DIR_ARG=""
fi

# Install protoc
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
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_VENV ]]; then
        echo "Creating mypy venv for Python $PY_VER_MYPY"
        uv venv -p "$PY_VER_MYPY" "$MYPY_VENV" --allow-existing
        uv pip install -p "$MYPY_VENV"  -r mypy_requirements.txt
    fi
    echo "Running mypy version:"
    "$MYPY_VENV"/bin/mypy --version
)

# Create unit tests venvs
for PY_VER in $PY_VER_UNIT_TESTS; do
    (
        UNIT_TESTS_VENV=venv_$PY_VER

        if [[ -z $SKIP_CLEAN ]] || [[ ! -e $UNIT_TESTS_VENV ]]; then
            uv venv -p "$PY_VER" "$UNIT_TESTS_VENV" --allow-existing
            uv pip install -p "$UNIT_TESTS_VENV"  -r test_requirements.txt
            # Install protobuf version override
            uv pip install -p "$UNIT_TESTS_VENV" "protobuf==$PYTHON_PROTOBUF_VERSION"
        fi
        "$UNIT_TESTS_VENV"/bin/py.test --version
    )
done

# Create mypy-protobuf venv
MYPY_PROTOBUF_VENV=venv_$PY_VER_MYPY_PROTOBUF
(
    # Create virtualenv + Install requirements for mypy-protobuf
    if [[ -z $SKIP_CLEAN ]] || [[ ! -e $MYPY_PROTOBUF_VENV ]]; then
        uv venv -p "$PY_VER_MYPY_PROTOBUF" "$MYPY_PROTOBUF_VENV" --allow-existing
        uv pip install -p "$MYPY_PROTOBUF_VENV" -e .
    fi
)

# Run mypy-protobuf
(
    source "$MYPY_PROTOBUF_VENV"/bin/activate

    # Confirm version number
    test "$(protoc-gen-mypy -V)" = "mypy-protobuf 4.0.0"
    test "$(protoc-gen-mypy --version)" = "mypy-protobuf 4.0.0"
    test "$(protoc-gen-mypy_grpc -V)" = "mypy-protobuf 4.0.0"
    test "$(protoc-gen-mypy_grpc --version)" = "mypy-protobuf 4.0.0"

    # Run mypy on mypy-protobuf internal code for developers to catch issues
    FILES="mypy_protobuf/main.py"
    "$MYPY_VENV/bin/mypy" ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --python-executable="$MYPY_PROTOBUF_VENV/bin/python3" --python-version="$PY_VER_MYPY_PROTOBUF_SHORT" $FILES

    # Generate protos
    python --version
    $PROTOC --version

    # CI Check to make sure generated files are committed
    SHA_BEFORE=$(find test/generated -name "*.pyi" -print0 | xargs -0 sha1sum)
    # Clean out generated/ directories - except for __init__.py
    find test/generated -type f -not -name "__init__.py" -delete
    find test/generated_sync_only -type f -not -name "__init__.py" -delete
    find test/generated_async_only -type f -not -name "__init__.py" -delete

    # Compile protoc -> python
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --python_out=test/generated

    # Compile protoc -> mypy using mypy_protobuf
    # Prereq - create the mypy.proto python proto
    find proto/mypy_protobuf -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --python_out=.
    find proto/mypy_protobuf -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=.

    # Sanity check that our flags work
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=quiet:test/generated
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=relax_strict_optional_primitives:test/generated
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=use_default_deprecation_warnings:test/generated
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=generate_concrete_servicer_stubs:test/generated

    if [[ "$READABLE_STUBS" == "1" ]]; then
        # Overwrite w/ run with mypy-protobuf with readable_stubs flag
        find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=readable_stubs:test/generated
        # Generate grpc protos
        find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_grpc_out=test/generated
    else
        # Overwrite w/ run with mypy-protobuf without flags
        find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=test/generated
        # Generate grpc protos
        find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_grpc_out=test/generated
    fi

    # Generate with concrete service stubs for testing
    find proto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_out=generate_concrete_servicer_stubs:test/generated_concrete
    find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_grpc_out=generate_concrete_servicer_stubs:test/generated_concrete

    # Generate with sync_only stubs for testing
    mkdir -p test/generated_sync_only
    find proto/testproto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_grpc_out=only_sync:test/generated_sync_only --mypy_out=test/generated_sync_only --python_out=test/generated_sync_only

    # Generate with async_only stubs for testing
    mkdir -p test/generated_async_only
    find proto/testproto -name "*.proto" -print0 | xargs -0 "$PROTOC" "${PROTOC_ARGS[@]}" --mypy_grpc_out=only_async:test/generated_async_only --mypy_out=test/generated_async_only --python_out=test/generated_async_only

    if [[ -n $VALIDATE ]] && ! diff <(echo "$SHA_BEFORE") <(find test/generated -name "*.pyi" -print0 | xargs -0 sha1sum); then
        echo -e "${RED}Some .pyi files did not match. Please commit those files${NC}"
        exit 1
    fi

    # if TEST_THIRD_PARTY is set to 1 then generate
    if [[ "$TEST_THIRD_PARTY" == "1" ]]; then
        PROTOBUF_REF=9eb9b36e8a6f0f2766e0fbb9263035642c66d49e
        GOOGLEAPIS_REF=d4a34bf03d617723146fe3ae15192c4d93981a27
        ENVOY_REF=87566c14a3f7667be0d6242cc482347a00365b23
        XDS_REF=ee656c7534f5d7dc23d44dd611689568f72017a6
        PROTOC_GEN_VALIDATE_REF=010dd2ce8153bdf39bfb97b2ef14de2212ee749a
        OPENTELEMETRY_PROTO_REF=b80501798339bf5cf4cb49c0027ee8d6bb03eae0
        CEL_SPEC_REF=121e265b0c5e1d4c7d5c140b33d6048fec754c77
        CLIENT_MODEL_REF=c6d074b66b267a90cd95607abd123add35b62dda

        mkdir -p third_party
        # Clone google protos
        git clone --filter=blob:none --sparse https://github.com/protocolbuffers/protobuf.git third_party/protobuf
        pushd third_party/protobuf
        git checkout $PROTOBUF_REF
        git sparse-checkout set src/google
        popd
        mkdir -p third_party/out/generated_protobuf
        find third_party/protobuf/src/google/protobuf  -maxdepth 1 -name "*.proto" \
            -print0 | xargs -0 "$PROTOC" --proto_path=third_party/protobuf/src --mypy_out=third_party/out/generated_protobuf --mypy_grpc_out=third_party/out/generated_protobuf --python_out=third_party/out/generated_protobuf
        # Clone googleapis protos
        git clone https://github.com/googleapis/googleapis.git third_party/googleapis
        pushd third_party/googleapis
        git checkout $GOOGLEAPIS_REF
        popd
        # Generate 3rd party protos
        mkdir -p third_party/out/generated_googleapis
        # Known conflict with extensions proto in googleapis - skip that one
        find third_party/googleapis -name "*.proto" \
            ! -path "third_party/googleapis/google/cloud/compute/v1/compute.proto" \
            ! -path "third_party/googleapis/google/cloud/compute/v1beta/compute.proto" \
            ! -path "third_party/googleapis/google/cloud/compute/v1small/compute_small.proto" \
            -print0 | xargs -0 "$PROTOC" --proto_path=third_party/googleapis --mypy_out=third_party/out/generated_googleapis --mypy_grpc_out=third_party/out/generated_googleapis --python_out=third_party/out/generated_googleapis

        # TODO: Use buf?
        git clone https://github.com/envoyproxy/envoy.git  --filter=blob:none --sparse third_party/envoy
        pushd third_party/envoy
        git checkout $ENVOY_REF
        git sparse-checkout set api
        popd
        git clone https://github.com/cncf/xds.git third_party/xds
        pushd third_party/xds
        git checkout $XDS_REF
        popd
        git clone https://github.com/bufbuild/protoc-gen-validate.git third_party/protoc-gen-validate
        pushd third_party/protoc-gen-validate
        git checkout $PROTOC_GEN_VALIDATE_REF
        popd
        git clone https://github.com/open-telemetry/opentelemetry-proto.git third_party/opentelemetry-proto
        pushd third_party/opentelemetry-proto
        git checkout $OPENTELEMETRY_PROTO_REF
        popd
        git clone https://github.com/google/cel-spec.git third_party/cel-spec
        pushd third_party/cel-spec
        git checkout $CEL_SPEC_REF
        popd
        git clone https://github.com/prometheus/client_model.git third_party/client_model
        pushd third_party/client_model
        git checkout $CLIENT_MODEL_REF
        popd

        mkdir -p third_party/out/generated_envoy
        find third_party -name "*.proto" \
            ! -path "third_party/protobuf/*" \
            ! -path "third_party/googleapis/google/cloud/compute/v1/compute.proto" \
            ! -path "third_party/googleapis/google/cloud/compute/v1beta/compute.proto" \
            ! -path "third_party/googleapis/google/cloud/compute/v1small/compute_small.proto" \
            -print0 | xargs -0 "$PROTOC" --proto_path=third_party/client_model --proto_path=third_party/cel-spec/proto --proto_path=third_party/opentelemetry-proto --proto_path=third_party/googleapis --proto_path=third_party/protoc-gen-validate --proto_path=third_party/envoy/api --proto_path=third_party/xds --mypy_out=third_party/out/generated_envoy --mypy_grpc_out=third_party/out/generated_envoy --python_out=third_party/out/generated_envoy
    fi
)

ERROR_FILE=$(mktemp)
trap 'rm -f "$ERROR_FILE"' EXIT

for PY_VER in $PY_VER_UNIT_TESTS; do
    UNIT_TESTS_VENV=venv_$PY_VER
    PY_VER_MYPY_TARGET=$(echo "$PY_VER" | cut -d. -f1-2)

    # Generate GRPC protos for mypy / tests
    (
        source "$UNIT_TESTS_VENV"/bin/activate
        find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 python -m grpc_tools.protoc "${PROTOC_ARGS[@]}" --grpc_python_out=test/generated
        find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 python -m grpc_tools.protoc "${PROTOC_ARGS[@]}" --grpc_python_out=test/generated_sync_only
        find proto/testproto/grpc -name "*.proto" -print0 | xargs -0 python -m grpc_tools.protoc "${PROTOC_ARGS[@]}" --grpc_python_out=test/generated_async_only
    )

    # Run mypy on unit tests / generated output
    (
        source "$MYPY_VENV"/bin/activate
        # Run concrete mypy
        CONCRETE_MODULES=( -m test.test_concrete )
        MYPYPATH=$MYPYPATH:test/generated_concrete mypy ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --no-incremental --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${CONCRETE_MODULES[@]}"

        # Run sync_only mypy
        SYNC_ONLY_MODULES=( -m test.sync_only.test_sync_only )
        MYPYPATH=$MYPYPATH:test/generated_sync_only mypy ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${SYNC_ONLY_MODULES[@]}"

        # Run async_only mypy
        ASYNC_ONLY_MODULES=( -m test.async_only.test_async_only )
        MYPYPATH=$MYPYPATH:test/generated_async_only mypy ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${ASYNC_ONLY_MODULES[@]}"

        if [[ "$TEST_THIRD_PARTY" == "1" ]]; then
            # Run thirdparty mypy
            GOOGLE=( third_party/out/generated_protobuf )
            MYPYPATH=$MYPYPATH:third_party/out/generated_protobuf mypy --explicit-package-bases ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${GOOGLE[@]}"
            GOOGLEAPIS=( third_party/out/generated_googleapis )
            MYPYPATH=$MYPYPATH:third_party/out/generated_googleapis mypy --explicit-package-bases ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${GOOGLEAPIS[@]}"
            ENVOY=( third_party/out/generated_envoy )
            MYPYPATH=$MYPYPATH:third_party/out/generated_envoy mypy --explicit-package-bases ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${ENVOY[@]}"
        fi

        export MYPYPATH=$MYPYPATH:test/generated

        # Run mypy
        MODULES=( -m test.test_generated_mypy -m test.test_grpc_usage -m test.test_grpc_async_usage )
        mypy ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --report-deprecated-as-note --no-incremental --python-executable="$UNIT_TESTS_VENV"/bin/python --python-version="$PY_VER_MYPY_TARGET" "${MODULES[@]}"

        # Run stubtest. Stubtest does not work with python impl - only cpp impl
        uv pip install -p "$MYPY_VENV" -r test_requirements.txt
        # Override python protobuf version
        uv pip install -p "$MYPY_VENV" "protobuf==$PYTHON_PROTOBUF_VERSION"
        API_IMPL="$(python3 -c "import google.protobuf.internal.api_implementation as a ; print(a.Type())")"
        if [[ $API_IMPL != "python" ]]; then
            # Skip stubtest for python version 3.13+ until positional argument decision is made
            if [[ "$PY_VER_MYPY" == "3.13.9" ]] || [[ "$PY_VER_MYPY" == "3.14.0" ]]; then
                echo "Skipping stubtest for Python $PY_VER_MYPY until positional argument decision is made"
            else
                PYTHONPATH=test/generated python3 -m mypy.stubtest ${CUSTOM_TYPESHED_DIR_ARG:+"$CUSTOM_TYPESHED_DIR_ARG"} --allowlist stubtest_allowlist.txt testproto
            fi
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
            # Copy over all the mypy results for the developer.
            call_mypy "$PY_VER" "${NEGATIVE_MODULES[@]}"
            cp "$MYPY_OUTPUT/mypy_output" "test_negative/output.expected.$PY_VER_MYPY_TARGET"
            cp "$MYPY_OUTPUT/mypy_output.omit_linenos" "test_negative/output.expected.$PY_VER_MYPY_TARGET.omit_linenos"

            # Record error instead of echoing and exiting
            echo "test_negative/output.expected.$PY_VER_MYPY_TARGET didnt match. Copying over for you." >> "$ERROR_FILE"
        fi
    )

    (
        # Run unit tests.
        source "$UNIT_TESTS_VENV"/bin/activate
        PYTHONPATH=test/generated py.test --ignore=test/generated --ignore=test/generated_sync_only --ignore=test/generated_async_only --ignore=third_party -v
    )
done


# Clean up third_party
rm -rf third_party

# Report all errors at the end
if [ -s "$ERROR_FILE" ]; then
    echo -e "\n${RED}===============================================${NC}"
    while IFS= read -r error; do
        echo -e "${RED}$error${NC}"
    done < "$ERROR_FILE"
    echo -e "${RED}Now rerun${NC}"
    exit 1
fi
