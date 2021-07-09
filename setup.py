import os
from setuptools import setup

def version():
    """Gets the version from mypy_protobuf/main.py
    Do not import mypy_protobuf.main directly, because an installed
    protobuf library may be loaded instead."""

    with open(os.path.join('mypy_protobuf', 'main.py')) as version_file:
        line = [v for v in version_file.readlines() if "__version__ =" in v][0]
        exec(line, globals())
        global __version__
        return __version__

setup(
    name="mypy-protobuf",
    version=version(),
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
    download_url="https://github.com/dropbox/mypy-protobuf/archive/v2.5.tar.gz",
    install_requires=["protobuf>=3.17.3"],
    entry_points={
        "console_scripts": [
            "protoc-gen-mypy = mypy_protobuf.main:main",
            "protoc-gen-mypy_grpc = mypy_protobuf.main:grpc",
        ],
    },
    scripts=["mypy_protobuf/protoc_gen_mypy.bat"],
    python_requires=">=3.6",
)
