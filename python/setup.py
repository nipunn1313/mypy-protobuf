from setuptools import setup

setup(
    name='mypy-protobuf',
    version='1.11',
    description='Generate mypy stub files from protobuf specs',
    keywords='mypy proto dropbox',
    license='Apache License 2.0',
    author='Nipunn Koorapati',
    author_email='nipunn@dropbox.com',
    py_modules=[],
    url='https://github.com/dropbox/mypy-protobuf',
    download_url='https://github.com/dropbox/mypy-protobuf/archive/v1.11.tar.gz',

    scripts=['protoc-gen-mypy', 'protoc_gen_mypy.bat'],
)
