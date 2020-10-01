mypy-protobuf: Generate mypy stub files from protobuf specs [![Build Status](https://travis-ci.org/dropbox/mypy-protobuf.svg?branch=master)](https://travis-ci.org/dropbox/mypy-protobuf)
===========================================================

## Requirements
protoc 3.0.0 or greater
python 2.7, 3.5, 3.6, 3.7 3.8
[python-protobuf >= 3.11.3](https://pypi.org/project/protobuf/3.7.1/)
[mypy >= v0.780](https://pypi.org/project/mypy)

Other configurations may work, but are not supported in testing currently. We would be open to expanding this list if a need arises - file an issue on the issue tracker.

## Python Implementation
There is a python implementation of the plugin in `python/protoc-gen-mypy`. On windows
you will have to use `python/protoc_gen_mypy.bat` for the executable.

The plugin can be installed with
```
pip install mypy-protobuf
```
On posix, ensure that the protoc-gen-mypy script installed onto your $PATH. Then run.
```
protoc --python_out=output/location --mypy_out=output/location
```
Alternately, you can explicitly provide the path:
```
protoc --plugin=protoc-gen-mypy=path/to/protoc-gen-mypy --python_out=output/location --mypy_out=output/location
```
On windows, provide the bat file:
```
protoc --plugin=protoc-gen-mypy=path/to/protoc_gen_mypy.bat --python_out=output/location --mypy_out=output/location
```
To suppress output, you can run
```
protoc --python_out=output/location --mypy_out=quiet:output/location
```

## Go Implementation
There is a go implementation of the plugin in `go/src/protoc-gen-mypy`.
The import sort order can be customized to split between stdlib and project protos
by changing the `project` const at the top of the file (we use dropbox since our
proto files are namespaced under dropbox/)

To build the plugin: `go get github.com/dropbox/mypy-protobuf/go/src/protoc-gen-mypy`.

The plugin can be used by adding the built target to the command line
when running `protoc` (in addition to the normal plugin for output languages).

## Support
Dropbox internally uses both implementations. We internally directly use the python implementation.
However, the go implementation here is a code drop from the Dropbox internal implementation with periodic
re-upstreams. As a result, the python implementation will get more timely support. We encourage community
contribution to improve quality/testing to bring both implementations to parity.

## Contributing
Contributions to the implementations are welcome. Please run tests using `./run_test.sh`.
Ensure code is formatted using black.
```
pip3 install black
black python/ test/
```

## Contributors

### Dropboxers
- [@nipunn1313](https://github.com/nipunn1313)
- [@dzbarsky](https://github.com/dzbarsky)
- [@gvanrossum](https://github.com/gvanrossum)
- [@peterlvilim](https://github.com/peterlvilim)
- [@msullivan](https://github.com/msullivan)
- [@bradenaw](https://github.com/bradenaw)

### Others
- [@Ketouem](https://github.com/Ketouem)
- [@nmiculinic](https://github.com/nmiculinic)
- [@onto](https://github.com/onto)
- [@jcppkkk](https://github.com/jcppkkk)
- [@drather19](https://github.com/drather19)
- [@smessmer](https://github.com/smessmer)
- [@pcorpet](https://github.com/pcorpet)
- [@zozoens31](https://github.com/zozoens31)
- [@abhishekrb19](https://github.com/abhishekrb19)
- [@jaens](https://github.com/jaens)
- [@arussellsaw](https://github.com/arussellsaw)
- [@shabbyrobe](https://github.com/shabbyrobe)
- [@reorx](https://github.com/reorx)
- [@zifter](https://github.com/zifter)
- [@juzna](https://github.com/juzna)
- [@mikolajz](https://github.com/mikolajz)
- [@chadrik](https://github.com/chadrik)
- [@EPronovost](https://github.com/EPronovost)


Licence etc.
------------

1. License: Apache 2.0.
2. Copyright attribution: Copyright (c) 2017 Dropbox, Inc.
3. External contributions to the project should be subject to
   Dropbox's Contributor License Agreement (CLA):
   https://opensource.dropbox.com/cla/
