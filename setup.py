import os
from setuptools import setup  # type: ignore[import]

def get_version() -> str:
    """Gets the version from mypy_protobuf/main.py
    Do not import mypy_protobuf.main directly, because an installed
    protobuf library may be loaded instead."""

    with open(os.path.join('mypy_protobuf', 'main.py')) as version_file:
        line = [v for v in version_file.readlines() if "__version__ =" in v][0]
        return line.split("=")[1].strip().strip("\"\'")

version = get_version()

setup(
    name="mypy-protobuf",
    version=version,
    description="Generate mypy stub files from protobuf specs",
    keywords="mypy proto dropbox",
    license="Apache License 2.0",
    author="Nipunn Koorapati",
    author_email="nipunn@dropbox.com",
    py_modules=[
        "mypy_protobuf",
        "mypy_protobuf.main",
        "mypy_protobuf.extensions_pb2",
    ],
    url="https://github.com/dropbox/mypy-protobuf",
    download_url="https://github.com/dropbox/mypy-protobuf/archive/v%s.tar.gz" % version,
    install_requires=[
        "protobuf>=3.17.3",
        "types-protobuf>=3.17.3",
        "grpcio-tools>=1.38.1",
    ],
    entry_points={
        "console_scripts": [
            "protoc-gen-mypy = mypy_protobuf.main:main",
            "protoc-gen-mypy_grpc = mypy_protobuf.main:grpc",
        ],
    },
    python_requires=">=3.6",
)
