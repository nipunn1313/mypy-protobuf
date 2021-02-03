#!/usr/bin/env python
"""Protoc Plugin to generate mypy stubs. Loosely based on @zbarsky's go implementation"""
import os

import sys
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Sequence,
    Tuple,
)

import google.protobuf.descriptor_pb2 as d
from google.protobuf.compiler import plugin_pb2 as plugin_pb2
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
from google.protobuf.internal.well_known_types import WKTBASES
from . import extensions_pb2


# So phabricator doesn't think mypy_protobuf.py is generated
GENERATED = "@ge" + "nerated"
HEADER = """\"\"\"
{} by mypy-protobuf.  Do not edit manually!
isort:skip_file
\"\"\"
""".format(
    GENERATED
)

# See https://github.com/dropbox/mypy-protobuf/issues/73 for details
PYTHON_RESERVED = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "async",
    "await",
    "assert",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}


def _mangle_global_identifier(name: str) -> str:
    """
    Module level identifiers are mangled and aliased so that they can be disambiguated
    from fields/enum variants with the same name within the file.

    Eg:
    Enum variant `Name` or message field `Name` might conflict with a top level
    message or enum named `Name`, so mangle it with a global___ prefix for
    internal references. Note that this doesn't affect inner enums/messages
    because they get fuly qualified when referenced within a file"""
    return "global___{}".format(name)


class Descriptors(object):
    def __init__(self, request: plugin_pb2.CodeGeneratorRequest) -> None:
        files = {f.name: f for f in request.proto_file}
        to_generate = {n: files[n] for n in request.file_to_generate}
        self.files: Dict[str, d.FileDescriptorProto] = files
        self.to_generate: Dict[str, d.FileDescriptorProto] = to_generate
        self.messages: Dict[str, d.DescriptorProto] = {}
        self.message_to_fd: Dict[str, d.FileDescriptorProto] = {}

        def _add_enums(
            enums: "RepeatedCompositeFieldContainer[d.EnumDescriptorProto]",
            prefix: str,
            _fd: d.FileDescriptorProto,
        ) -> None:
            for enum in enums:
                self.message_to_fd[prefix + enum.name] = _fd
                self.message_to_fd[prefix + enum.name + ".V"] = _fd

        def _add_messages(
            messages: "RepeatedCompositeFieldContainer[d.DescriptorProto]",
            prefix: str,
            _fd: d.FileDescriptorProto,
        ) -> None:
            for message in messages:
                self.messages[prefix + message.name] = message
                self.message_to_fd[prefix + message.name] = _fd
                sub_prefix = prefix + message.name + "."
                _add_messages(message.nested_type, sub_prefix, _fd)
                _add_enums(message.enum_type, sub_prefix, _fd)

        for fd in request.proto_file:
            start_prefix = "." + fd.package + "." if fd.package else "."
            _add_messages(fd.message_type, start_prefix, fd)
            _add_enums(fd.enum_type, start_prefix, fd)


class PkgWriter(object):
    """Writes a single pyi file"""

    def __init__(
        self,
        fd: d.FileDescriptorProto,
        descriptors: Descriptors,
        readable_stubs: bool,
        relax_strict_optional_primitives: bool,
    ) -> None:
        self.fd = fd
        self.descriptors = descriptors
        self.readable_stubs = readable_stubs
        self.relax_strict_optional_primitives = relax_strict_optional_primitives
        self.lines: List[str] = []
        self.indent = ""

        # Set of {x}, where {x} corresponds to to `import {x}`
        self.imports: Set[str] = set()
        # dictionary of x->(y,z) for `from {x} import {y} as {z}`
        # if {z} is None, then it shortens to `from {x} import {y}`
        self.from_imports: Dict[str, Set[Tuple[str, Optional[str]]]] = defaultdict(set)
        self.locals: Set[str] = set()

    def _import(self, path: str, name: str) -> str:
        """Imports a stdlib path and returns a handle to it
        eg. self._import("typing", "Optional") -> "Optional"
        """
        imp = path.replace("/", ".")
        if self.readable_stubs:
            self.from_imports[imp].add((name, None))
            return name
        else:
            self.imports.add(imp)
            return imp + "." + name

    def _import_message(self, name: str) -> str:
        """Import a referenced message and return a handle"""
        message_fd = self.descriptors.message_to_fd[name]
        assert message_fd.name.endswith(".proto")

        # Strip off package name
        if message_fd.package:
            assert name.startswith("." + message_fd.package + ".")
            name = name[len("." + message_fd.package + ".") :]
        else:
            assert name.startswith(".")
            name = name[1:]

        # Message defined in this file.
        if message_fd.name == self.fd.name:
            return name if self.readable_stubs else _mangle_global_identifier(name)

        # Not in file. Must import
        # Python generated code ignores proto packages, so the only relevant factor is
        # whether it is in the file or not.
        split = name.split(".")
        import_name = self._import(
            message_fd.name[:-6].replace("-", "_") + "_pb2", split[0]
        )
        remains = ".".join(split[1:])
        if not remains:
            return import_name
        # remains could either be a direct import of a nested enum or message
        # from another package.
        return import_name + "." + remains

    def _builtin(self, name: str) -> str:
        return self._import("builtins", name)

    @contextmanager
    def _indent(self) -> Generator:
        self.indent = self.indent + "    "
        yield
        self.indent = self.indent[:-4]

    def _write_line(self, line: str, *args: Any) -> None:
        if line == "":
            self.lines.append(line)
        else:
            self.lines.append(self.indent + line.format(*args))

    def write_enum_values(self, enum: d.EnumDescriptorProto, value_type: str) -> None:
        for val in enum.value:
            if val.name in PYTHON_RESERVED:
                continue

            self._write_line(
                "{} = {}({})",
                val.name,
                value_type,
                val.number,
            )

    def write_module_attributes(self) -> None:
        l = self._write_line
        l(
            "DESCRIPTOR: {} = ...",
            self._import("google.protobuf.descriptor", "FileDescriptor"),
        )
        l("")

    def write_enums(
        self, enums: Iterable[d.EnumDescriptorProto], prefix: str = ""
    ) -> None:
        l = self._write_line
        for enum in [e for e in enums if e.name not in PYTHON_RESERVED]:
            if prefix == "" and not self.readable_stubs:
                l("{} = {}", _mangle_global_identifier(enum.name), enum.name)
            l(
                "class {}({}[{}], {}):",
                "_" + enum.name,
                self._import(
                    "google.protobuf.internal.enum_type_wrapper", "_EnumTypeWrapper"
                ),
                enum.name + ".V",
                self._builtin("type"),
            )
            with self._indent():
                l(
                    "DESCRIPTOR: {} = ...",
                    self._import("google.protobuf.descriptor", "EnumDescriptor"),
                )
                self.write_enum_values(enum, prefix + enum.name + ".V")

            l("class {}(metaclass={}):", enum.name, "_" + enum.name)
            with self._indent():
                l(
                    "V = {}('V', {})",
                    self._import("typing", "NewType"),
                    self._builtin("int"),
                )

            self.write_enum_values(enum, prefix + enum.name + ".V")
            l("")

    def write_messages(
        self, messages: Iterable[d.DescriptorProto], prefix: str
    ) -> None:
        l = self._write_line

        for desc in [m for m in messages if m.name not in PYTHON_RESERVED]:
            self.locals.add(desc.name)
            qualified_name = prefix + desc.name

            # Reproduce some hardcoded logic from the protobuf implementation - where
            # some specific "well_known_types" generated protos to have additional
            # base classes
            addl_base = u""
            if self.fd.package + "." + desc.name in WKTBASES:
                # chop off the .proto - and import the well known type
                # eg `from google.protobuf.duration import Duration`
                well_known_type = WKTBASES[self.fd.package + "." + desc.name]
                addl_base = ", " + self._import(
                    "google.protobuf.internal.well_known_types",
                    well_known_type.__name__,
                )

            message_class = self._import("google.protobuf.message", "Message")
            l("class {}({}{}):", desc.name, message_class, addl_base)
            with self._indent():
                l(
                    "DESCRIPTOR: {} = ...",
                    self._import("google.protobuf.descriptor", "Descriptor"),
                )

                # Nested enums/messages
                self.write_enums(desc.enum_type, qualified_name + ".")
                self.write_messages(desc.nested_type, qualified_name + ".")
                fields = [f for f in desc.field if f.name not in PYTHON_RESERVED]

                # Scalar fields
                for field in [f for f in fields if is_scalar(f)]:
                    if field.label == d.FieldDescriptorProto.LABEL_REPEATED:
                        container = self._import(
                            "google.protobuf.internal.containers",
                            "RepeatedScalarFieldContainer",
                        )
                        l(
                            "{}: {}[{}] = ...",
                            field.name,
                            container,
                            self.python_type(field),
                        )
                    else:
                        l("{}: {} = ...", field.name, self.python_type(field))
                l("")

                # Getters for non-scalar fields
                for field in [f for f in fields if not is_scalar(f)]:
                    l("@property")
                    if field.label == d.FieldDescriptorProto.LABEL_REPEATED:
                        msg = self.descriptors.messages[field.type_name]
                        if msg.options.map_entry:
                            # map generates a special Entry wrapper message
                            if is_scalar(msg.field[1]):
                                container = self._import(
                                    "google.protobuf.internal.containers", "ScalarMap"
                                )
                            else:
                                container = self._import(
                                    "google.protobuf.internal.containers", "MessageMap"
                                )
                            ktype, vtype = self._map_key_value_types(
                                field, msg.field[0], msg.field[1]
                            )
                            l(
                                "def {}(self) -> {}[{}, {}]: ...",
                                field.name,
                                container,
                                ktype,
                                vtype,
                            )
                        else:
                            container = self._import(
                                "google.protobuf.internal.containers",
                                "RepeatedCompositeFieldContainer",
                            )
                            l(
                                "def {}(self) -> {}[{}]: ...",
                                field.name,
                                container,
                                self.python_type(field),
                            )
                    else:
                        l(
                            "def {}(self) -> {}: ...",
                            field.name,
                            self.python_type(field),
                        )
                    l("")

                for ext in desc.extension:
                    l(
                        "{}: {}[{}, {}] = ...",
                        ext.name,
                        self._import(
                            "google.protobuf.internal.extension_dict",
                            "_ExtensionFieldDescriptor",
                        ),
                        self._import_message(ext.extendee),
                        self.python_type(ext),
                    )
                    l("")

                # Constructor
                self_arg = "self_" if any(f.name == "self" for f in fields) else "self"
                l("def __init__({},", self_arg)
                with self._indent():
                    if len(fields) > 0:
                        # Only positional args allowed
                        # See https://github.com/dropbox/mypy-protobuf/issues/71
                        l("*,")
                    for field in [f for f in fields]:
                        if field.label == d.FieldDescriptorProto.LABEL_REPEATED:
                            if (
                                field.type_name in self.descriptors.messages
                                and self.descriptors.messages[
                                    field.type_name
                                ].options.map_entry
                            ):
                                msg = self.descriptors.messages[field.type_name]
                                ktype, vtype = self._map_key_value_types(
                                    field, msg.field[0], msg.field[1]
                                )
                                l(
                                    "{} : {}[{}[{}, {}]] = ...,",
                                    field.name,
                                    self._import("typing", "Optional"),
                                    self._import("typing", "Mapping"),
                                    ktype,
                                    vtype,
                                )
                            else:
                                l(
                                    "{} : {}[{}[{}]] = ...,",
                                    field.name,
                                    self._import("typing", "Optional"),
                                    self._import("typing", "Iterable"),
                                    self.python_type(field),
                                )
                        elif (
                            self.fd.syntax == "proto3"
                            and is_scalar(field)
                            and not self.relax_strict_optional_primitives
                        ):
                            l(
                                "{} : {} = ...,",
                                field.name,
                                self.python_type(field),
                            )
                        else:
                            l(
                                "{} : {}[{}] = ...,",
                                field.name,
                                self._import("typing", "Optional"),
                                self.python_type(field),
                            )
                    l(") -> None: ...")

                self.write_stringly_typed_fields(desc)

            if prefix == "" and not self.readable_stubs:
                l("{} = {}", _mangle_global_identifier(desc.name), desc.name)
            l("")

    def write_stringly_typed_fields(self, desc: d.DescriptorProto) -> None:
        """Type the stringly-typed methods as a Union[Literal, Literal ...]"""
        l = self._write_line
        # HasField, ClearField, WhichOneof accepts both bytes/unicode
        # HasField only supports singular. ClearField supports repeated as well
        # In proto3, HasField only supports message fields and optional fields
        # HasField always supports oneof fields
        hf_fields = [
            f.name
            for f in desc.field
            if f.HasField("oneof_index")
            or (
                f.label != d.FieldDescriptorProto.LABEL_REPEATED
                and (
                    self.fd.syntax != "proto3"
                    or f.type == d.FieldDescriptorProto.TYPE_MESSAGE
                    or f.proto3_optional
                )
            )
        ]
        cf_fields = [f.name for f in desc.field]
        wo_fields = {
            oneof.name: [
                f.name
                for f in desc.field
                if f.HasField("oneof_index") and f.oneof_index == idx
            ]
            for idx, oneof in enumerate(desc.oneof_decl)
        }

        hf_fields.extend(wo_fields.keys())
        cf_fields.extend(wo_fields.keys())

        hf_fields_text = ",".join(
            sorted('u"{}",b"{}"'.format(name, name) for name in hf_fields)
        )
        cf_fields_text = ",".join(
            sorted('u"{}",b"{}"'.format(name, name) for name in cf_fields)
        )

        if not hf_fields and not cf_fields and not wo_fields:
            return

        if hf_fields:
            l(
                "def HasField(self, field_name: {}[{}]) -> {}: ...",
                self._import("typing_extensions", "Literal"),
                hf_fields_text,
                self._builtin("bool"),
            )
        if cf_fields:
            l(
                "def ClearField(self, field_name: {}[{}]) -> None: ...",
                self._import("typing_extensions", "Literal"),
                cf_fields_text,
            )

        for wo_field, members in sorted(wo_fields.items()):
            if len(wo_fields) > 1:
                l("@{}", self._import("typing", "overload"))
            l(
                "def WhichOneof(self, oneof_group: {}[{}]) -> {}[{}]: ...",
                self._import("typing_extensions", "Literal"),
                # Accepts both unicode and bytes in both py2 and py3
                'u"{}",b"{}"'.format(wo_field, wo_field),
                self._import("typing_extensions", "Literal"),
                # Returns `str` in both py2 and py3 (bytes in py2, unicode in py3)
                ",".join('"{}"'.format(m) for m in members),
            )

    def write_extensions(self, extensions: Sequence[d.FieldDescriptorProto]) -> None:
        if not extensions:
            return
        l = self._write_line
        field_descriptor_class = self._import(
            "google.protobuf.descriptor", "FieldDescriptor"
        )
        for extension in extensions:
            l("{}: {} = ...", extension.name, field_descriptor_class)
            l("")

    def write_methods(
        self, service: d.ServiceDescriptorProto, is_abstract: bool
    ) -> None:
        l = self._write_line
        methods = [m for m in service.method if m.name not in PYTHON_RESERVED]
        if not methods:
            l("pass")
        for method in methods:
            if is_abstract:
                l("@{}", self._import("abc", "abstractmethod"))
            l("def {}(self,", method.name)
            with self._indent():
                l(
                    "rpc_controller: {},",
                    self._import("google.protobuf.service", "RpcController"),
                )
                l("request: {},", self._import_message(method.input_type))
                l(
                    "done: {}[{}[[{}], None]],",
                    self._import("typing", "Optional"),
                    self._import("typing", "Callable"),
                    self._import_message(method.output_type),
                )
            l(
                ") -> {}[{}]: ...",
                self._import("concurrent.futures", "Future"),
                self._import_message(method.output_type),
            )

    def write_services(self, services: Iterable[d.ServiceDescriptorProto]) -> None:
        l = self._write_line
        for service in [s for s in services if s.name not in PYTHON_RESERVED]:
            # The service definition interface
            l(
                "class {}({}, metaclass={}):",
                service.name,
                self._import("google.protobuf.service", "Service"),
                self._import("abc", "ABCMeta"),
            )
            with self._indent():
                self.write_methods(service, is_abstract=True)

            # The stub client
            l("class {}({}):", service.name + "_Stub", service.name)
            with self._indent():
                l(
                    "def __init__(self, rpc_channel: {}) -> None: ...",
                    self._import("google.protobuf.service", "RpcChannel"),
                )
                self.write_methods(service, is_abstract=False)

    def _import_casttype(self, casttype: str) -> str:
        split = casttype.split(".")
        assert (
            len(split) == 2
        ), "mypy_protobuf.[casttype,keytype,valuetype] is expected to be of format path/to/file.TypeInFile"
        pkg = split[0].replace("/", ".")
        return self._import(pkg, split[1])

    def _map_key_value_types(
        self,
        map_field: d.FieldDescriptorProto,
        key_field: d.FieldDescriptorProto,
        value_field: d.FieldDescriptorProto,
    ) -> Tuple[str, str]:
        key_casttype = map_field.options.Extensions[extensions_pb2.keytype]
        ktype = (
            self._import_casttype(key_casttype)
            if key_casttype
            else self.python_type(key_field)
        )
        value_casttype = map_field.options.Extensions[extensions_pb2.valuetype]
        vtype = (
            self._import_casttype(value_casttype)
            if value_casttype
            else self.python_type(value_field)
        )
        return ktype, vtype

    def _input_type(self, method: d.MethodDescriptorProto) -> str:
        result = self._import_message(method.input_type)
        if method.client_streaming:
            result = "{}[{}]".format(self._import("typing", "Iterator"), result)
        return result

    def _output_type(self, method: d.MethodDescriptorProto) -> str:
        result = self._import_message(method.output_type)
        if method.server_streaming:
            result = "{}[{}]".format(self._import("typing", "Iterator"), result)
        return result

    def write_grpc_methods(self, service: d.ServiceDescriptorProto) -> None:
        l = self._write_line
        methods = [m for m in service.method if m.name not in PYTHON_RESERVED]
        if not methods:
            l("pass")
            l("")
        for method in methods:
            l("@{}", self._import("abc", "abstractmethod"))
            l("def {}(self,", method.name)
            with self._indent():
                l("request: {},", self._input_type(method))
                l("context: {},", self._import("grpc", "ServicerContext"))
            l(") -> {}: ...", self._output_type(method))
            l("")

    def write_grpc_stub_methods(self, service: d.ServiceDescriptorProto) -> None:
        l = self._write_line
        methods = [m for m in service.method if m.name not in PYTHON_RESERVED]
        if not methods:
            l("pass")
            l("")
        for method in methods:
            l("def {}(self,", method.name)
            with self._indent():
                l("request: {},", self._input_type(method))
            l(") -> {}: ...", self._output_type(method))
            l("")

    def write_grpc_services(self, services: Iterable[d.ServiceDescriptorProto]) -> None:
        l = self._write_line
        l(
            "from .{} import *",
            self.fd.name.rsplit("/", 1)[-1][:-6].replace("-", "_") + "_pb2",
        )

        for service in [s for s in services if s.name not in PYTHON_RESERVED]:
            # The stub client
            l("class {}Stub:", service.name)
            with self._indent():
                l(
                    "def __init__(self, channel: {}) -> None: ...",
                    self._import("grpc", "Channel"),
                )
                self.write_grpc_stub_methods(service)
            l("")
            # The service definition interface
            l(
                "class {}Servicer(metaclass={}):",
                service.name,
                self._import("abc", "ABCMeta"),
            )
            with self._indent():
                self.write_grpc_methods(service)
            l("")
            l(
                "def add_{}Servicer_to_server(servicer: {}Servicer, server: {}) -> None: ...",
                service.name,
                service.name,
                self._import("grpc", "Server"),
            )
            l("")

    def python_type(self, field: d.FieldDescriptorProto) -> str:
        casttype = field.options.Extensions[extensions_pb2.casttype]
        if casttype:
            return self._import_casttype(casttype)

        mapping: Dict[d.FieldDescriptorProto.TypeValue, Callable[[], str]] = {
            d.FieldDescriptorProto.TYPE_DOUBLE: lambda: self._builtin("float"),
            d.FieldDescriptorProto.TYPE_FLOAT: lambda: self._builtin("float"),
            d.FieldDescriptorProto.TYPE_INT64: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_UINT64: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_FIXED64: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_SFIXED64: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_SINT64: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_INT32: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_UINT32: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_FIXED32: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_SFIXED32: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_SINT32: lambda: self._builtin("int"),
            d.FieldDescriptorProto.TYPE_BOOL: lambda: self._builtin("bool"),
            d.FieldDescriptorProto.TYPE_STRING: lambda: self._import("typing", "Text"),
            d.FieldDescriptorProto.TYPE_BYTES: lambda: self._builtin("bytes"),
            d.FieldDescriptorProto.TYPE_ENUM: lambda: self._import_message(
                field.type_name + ".V"
            ),
            d.FieldDescriptorProto.TYPE_MESSAGE: lambda: self._import_message(
                field.type_name
            ),
            d.FieldDescriptorProto.TYPE_GROUP: lambda: self._import_message(
                field.type_name
            ),
        }

        assert field.type in mapping, "Unrecognized type: " + repr(field.type)
        return mapping[field.type]()

    def write(self) -> str:
        for reexport_idx in self.fd.public_dependency:
            reexport_file = self.fd.dependency[reexport_idx]
            reexport_fd = self.descriptors.files[reexport_file]
            reexport_imp = (
                reexport_file[:-6].replace("-", "_").replace("/", ".") + "_pb2"
            )
            names = (
                [m.name for m in reexport_fd.message_type]
                + [m.name for m in reexport_fd.enum_type]
                + [m.name for m in reexport_fd.extension]
            )
            if reexport_fd.options.py_generic_services:
                names.extend(m.name for m in reexport_fd.service)

            if names:
                # n,n to force a reexport (from x import y as y)
                self.from_imports[reexport_imp].update((n, n) for n in names)

        import_lines = []
        for pkg in sorted(self.imports):
            import_lines.append(u"import {}".format(pkg))

        for pkg, items in sorted(self.from_imports.items()):
            import_lines.append(u"from {} import (".format(pkg))
            for (name, reexport_name) in sorted(items):
                if reexport_name is None:
                    import_lines.append(u"    {},".format(name))
                else:
                    import_lines.append(u"    {} as {},".format(name, reexport_name))
            import_lines.append(u")\n")
        import_lines.append("")

        return "\n".join(import_lines + self.lines)


def is_scalar(fd: d.FieldDescriptorProto) -> bool:
    return not (
        fd.type == d.FieldDescriptorProto.TYPE_MESSAGE
        or fd.type == d.FieldDescriptorProto.TYPE_GROUP
    )


def generate_mypy_stubs(
    descriptors: Descriptors,
    response: plugin_pb2.CodeGeneratorResponse,
    quiet: bool,
    readable_stubs: bool,
    relax_strict_optional_primitives: bool,
) -> None:
    for name, fd in descriptors.to_generate.items():
        pkg_writer = PkgWriter(
            fd, descriptors, readable_stubs, relax_strict_optional_primitives
        )
        pkg_writer.write_module_attributes()
        pkg_writer.write_enums(fd.enum_type)
        pkg_writer.write_messages(fd.message_type, "")
        pkg_writer.write_extensions(fd.extension)
        if fd.options.py_generic_services:
            pkg_writer.write_services(fd.service)

        assert name == fd.name
        assert fd.name.endswith(".proto")
        output = response.file.add()
        output.name = fd.name[:-6].replace("-", "_").replace(".", "/") + "_pb2.pyi"
        output.content = HEADER + pkg_writer.write()
        if not quiet:
            print("Writing mypy to", output.name, file=sys.stderr)


def generate_mypy_grpc_stubs(
    descriptors: Descriptors,
    response: plugin_pb2.CodeGeneratorResponse,
    quiet: bool,
    readable_stubs: bool,
    relax_strict_optional_primitives: bool,
) -> None:
    for name, fd in descriptors.to_generate.items():
        pkg_writer = PkgWriter(
            fd, descriptors, readable_stubs, relax_strict_optional_primitives
        )
        pkg_writer.write_grpc_services(fd.service)

        assert name == fd.name
        assert fd.name.endswith(".proto")
        output = response.file.add()
        output.name = fd.name[:-6].replace("-", "_").replace(".", "/") + "_pb2_grpc.pyi"
        output.content = HEADER + pkg_writer.write()
        if not quiet:
            print("Writing mypy to", output.name, file=sys.stderr)


@contextmanager
def code_generation() -> Generator[
    Tuple[plugin_pb2.CodeGeneratorRequest, plugin_pb2.CodeGeneratorResponse], None, None
]:
    # Read request message from stdin
    data = sys.stdin.buffer.read()

    # Parse request
    request = plugin_pb2.CodeGeneratorRequest()
    request.ParseFromString(data)

    # Create response
    response = plugin_pb2.CodeGeneratorResponse()

    # Declare support for optional proto3 fields
    response.supported_features |= (
        plugin_pb2.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL
    )

    yield request, response

    # Serialise response message
    output = response.SerializeToString()

    # Write to stdout
    sys.stdout.buffer.write(output)


def main() -> None:
    # Generate mypy
    with code_generation() as (request, response):
        generate_mypy_stubs(
            Descriptors(request),
            response,
            "quiet" in request.parameter,
            "readable_stubs" in request.parameter,
            "relax_strict_optional_primitives" in request.parameter,
        )


def grpc() -> None:
    # Generate grpc mypy
    with code_generation() as (request, response):
        generate_mypy_grpc_stubs(
            Descriptors(request),
            response,
            "quiet" in request.parameter,
            "readable_stubs" in request.parameter,
            "relax_strict_optional_primitives" in request.parameter,
        )


if __name__ == "__main__":
    main()
