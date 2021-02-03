mypy-protobuf: Generate mypy stub files from protobuf specs

[![CI](https://github.com/dropbox/mypy-protobuf/workflows/CI/badge.svg)](https://github.com/dropbox/mypy-protobuf/actions?query=branch%3Amaster)
[![pypi](https://img.shields.io/pypi/v/mypy-protobuf?logo=Pypi)](https://pypi.org/project/mypy-protobuf/)
[![license](https://img.shields.io/github/license/dropbox/mypy-protobuf)](https://github.com/dropbox/mypy-protobuf/blob/master/LICENSE)
===========================================================

We just released a new major release mypy-protobuf 2. on 02/02/2021! It includes some backward incompatible changes.
See [Changelog](CHANGELOG.md) for recent changes.

## Requirements

[mypy >= v0.800](https://pypi.org/project/mypy)
[protoc](https://github.com/protocolbuffers/protobuf/releases) 3.14.0 or greater
[python-protobuf >= 3.14.0](https://pypi.org/project/protobuf/)
[python >= 3.6](https://www.python.org/downloads/source/) - for running mypy-protobuf plugin. Generated stubs will compatible back to python2.

Other configurations may work, but are not supported in testing currently. We would be open to expanding this list if a need arises - file an issue on the issue tracker.

## Installation

The plugin can be installed with
```
pip install mypy-protobuf
```
To install unreleased
```
REV=master  # or whichever unreleased git rev you'd like
pip install git+https://github.com/dropbox/mypy-protobuf.git@$REV

# Prior to directory structure flattening, you may need
pip install git+https://github.com/dropbox/mypy-protobuf.git@$REV#subdirectory=python
```

## Implementation
The implementation of the plugin is in `mypy_protobuf/main.py`, which installs to
a posix executable protoc-gen-mypy.
On windows you will have to use `protoc_gen_mypy.bat` for the executable.

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

## Features

See [Changelog](CHANGELOG.md) for full listing

### Types enum int values more strongly

Enum int values produce stubs which wrap the int values in NewType
```
enum MyEnum {
  FOO = 0;
  BAR = 1;
}
```
Will yield an [enum type wrapper](https://github.com/python/typeshed/blob/16ae4c61201cd8b96b8b22cdfb2ab9e89ba5bcf2/stubs/protobuf/google/protobuf/internal/enum_type_wrapper.pyi) whose methods type to `MyEnum.V` rather than `int`.
This allows mypy to catch bugs where the wrong enum value is being used.

mypy-protobuf  autogenerates an instance of the EnumTypeWrapper as follows.

```
class _MyEnum(google.protobuf.internal.EnumTypeWrapper[MyEnum.V], builtins.type):
    DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
    FOO = MyEnum.V(0)
    BAR = MyEnum.V(1)
class MyEnum(metaclass=_OuterEnum):
    V = typing___NewType('V', builtins.int)
FOO = MyEnum.V(0)
BAR = MyEnum.V(1)
```

Calling code may be typed as follows. Note that the type of `x` must be quoted
until [upstream protobuf](https://github.com/protocolbuffers/protobuf/pull/8182) supports `V`
```
def f(x: 'MyEnum.V'):
    print(x)

f(MyEnum.Value("FOO"))
```

### Supports generating type wrappers for fields and maps

M.proto
```
message M {
  uint32 user_id = 1 [(mypy_protobuf.casttype)="mymod.UserId"
  map<uint32, string> email_by_uid = 2 [
    (mypy_protobuf.keytype)="path/to/mymod.UserId",
    (mypy_protobuf.valuetype)="path/to/mymod.Email"
  ];
}
```
mymod.py
```
UserId = NewType("UserId", int)
Email = NewType("Email", Text)
```

### `py_generic_services`
If `py_generic_services` is set in your proto file, then mypy-protobuf will
generate service stubs. If you want GRPC stubs instead - use the GRPC instructions.

### `readable_stubs`
If `readable_stubs` is set, mypy-protobuf will generate easier-to-read stubs. The downside
to this approach - is that it's possible to generate stubs which do not pass mypy - particularly
in the case of name collisions. mypy-protobuf defaults to generating stubs with fully qualified
imports and mangled global-level identifiers to defend against name collisions between global
identifiers and field names.

If you're ok with this risk, try it out!
```
protoc --python_out=output/location --mypy_out=readable_stubs:output/location
```

### `relax_strict_optional_primitives`

If you are using proto3, then primitives cannot be represented as NULL on the wire -
only as their zero value. By default mypy-protobuf types message constructors to have
non-nullable primitives (eg `int` instead of `Optional[int]`). python-protobuf itself will
internally convert None -> zero value, and if you intentionally want to use this behavior,
set this! We recommend avoiding this, but it may be helpful when migrating existing proto2 code.

```
protoc --python_out=output/location --mypy_out=relax_strict_optional_primitives:output/location
```

### Output suppression
To suppress output, you can run
```
protoc --python_out=output/location --mypy_out=quiet:output/location
```

## GRPC

This plugin provides stubs generation for grpcio generated code.
```
protoc \
    --python_out=output/location \
    --mypy_out=output/location \
    --grpc_out=output/location \
    --mypy_grpc_out=output/location
```

Note that generated code for grpc will work only together with code for python and locations should be the same.
If you need stubs for grpc internal code we suggest using this package https://github.com/shabbyrobe/grpc-stubs 


## Contributing
Contributions to the implementation are welcome. Please run tests using `./run_test.sh`.
Ensure code is formatted using black.
```
pip3 install black
black mypy_protobuf/main.py test/
```

## Contributors

### Dropboxers
- [@nipunn1313](https://github.com/nipunn1313)
- [@dzbarsky](https://github.com/dzbarsky)
- [@gvanrossum](https://github.com/gvanrossum)
- [@peterlvilim](https://github.com/peterlvilim)
- [@msullivan](https://github.com/msullivan)
- [@bradenaw](https://github.com/bradenaw)
- [@ilevkivskyi](https://github.com/ilevkivskyi)

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
- [@chrislawlor](https://github.com/chrislawlor)
- [@henribru](https://github.com/henribru)
- [@Evgenus](https://github.com/Evgenus)

Licence etc.
------------

1. License: Apache 2.0.
2. Copyright attribution: Copyright (c) 2017 Dropbox, Inc.
3. External contributions to the project should be subject to
   Dropbox's Contributor License Agreement (CLA):
   https://opensource.dropbox.com/cla/
