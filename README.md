mypy-protobuf: Generate mypy stub files from protobuf specs
===========================================================

There is a go implementation of the plugin in `go/src/protoc-gen-mypy`.
The import sort order can be customized to split between stdlib and project protos
by changing the `project` const at the top of the file (we use dropbox since our
proto files are namespaced under dropbox/)

To build the plugin:
  1. Configure GOPATH to point to the `go` directory of this repo.
  2. Configure GOROOT (if your go compiler is before 1.8)
  3. `git clone https://github.com/gogo/protobuf.git go/src/github.com/gogo/protobuf`
  4. `go build go/src/protoc-gen-mypy/main.go`

The plugin can be used by adding the built target to the command line
when running `protoc` (in addition to the normal plugin for output languages).

There is a python implementation in the plugin in `python/protoc-gen-mypy`. On windows
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

Licence etc.
------------

1. License: Apache 2.0.
2. Copyright attribution: Copyright (c) 2017 Dropbox, Inc.
3. External contributions to the project should be subject to
   Dropbox's Contributor License Agreement (CLA):
   https://opensource.dropbox.com/cla/
