mypy-protobuf: Generate mypy stub files from protobuf specs
===========================================================

There is a go implementation of the plugin in `go/src/protoc-gen-mypy`.
The import sort order can be customized to split between stdlib and project protos
by changing the `project` const at the top of the file (we use dropbox since our
proto files are namespaced under dropbox/)

To build the plugin:
  1. Configure GOPATH to point to the `go` directory of this repo.
  2. Configure GOROOT (if your go compiler is before 1.8)
  3. Clone github.com/gogo/protobuf to go/src/github.com/gogo/protobuf/
  4. `go build go/src/protoc-gen-mypy/main.go`

The plugin can be used by adding the built target to the command line
when running `protoc` (in addition to the normal plugin for output languages).

Licence etc.
------------

1. License: Apache 2.0.
2. Copyright attribution: Copyright (c) 2017 Dropbox, Inc.
3. External contributions to the project should be subject to
   Dropbox's Contributor License Agreement (CLA):
   https://opensource.dropbox.com/cla/
