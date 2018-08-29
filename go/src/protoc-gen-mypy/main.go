package main

import (
	"fmt"
	"path"
	"sort"
	"strings"

	"proto/mypy"

	"github.com/gogo/protobuf/proto"
	"github.com/gogo/protobuf/protoc-gen-gogo/descriptor"
	"github.com/gogo/protobuf/protoc-gen-gogo/generator"
	plugin "github.com/gogo/protobuf/protoc-gen-gogo/plugin"
	"github.com/gogo/protobuf/vanity/command"
)

// Note: This const is used to group imports between project and stdlib. Replace as appropriate.
const project = "dropbox"

const protoContainersPkg = "google/protobuf/internal/containers"

// these are reserved names.
var (
	// If a class has exactly this name, we will prefix the class name
	// with _, then create an alias to it, to avoid collision when referencing it
	reservedNames       = []string{"Name", "Value"}
	reservedMethodNames = map[string]struct{}{
		"Close": struct{}{},
	}
)

// Python import handling
type ImportName struct {
	name  string
	alias string
}

func (n *ImportName) String() string {
	return n.alias
}

type nestedImport struct {
	importName *ImportName
	message    string
	// deadcode: alias is grandfathered in as legacy code
	alias string
}

func (n *nestedImport) String() string {
	return n.importName.alias + "." + n.message
}

func NewNestedImport(importName *ImportName, message string) *nestedImport {
	return &nestedImport{
		importName: importName,
		message:    message,
	}
}

type PythonPkgMap struct {
	// package -> name
	imports map[string]map[string]*ImportName
	locals  []string
}

func NewPythonPkgMap() *PythonPkgMap {
	return &PythonPkgMap{
		imports: make(map[string]map[string]*ImportName),
		locals:  make([]string, 0),
	}
}

func (m *PythonPkgMap) From(path string, name string) *ImportName {
	if strings.HasSuffix(path, ".py") {
		path = path[:len(path)-3]
	} else if strings.HasSuffix(path, ".proto") {
		path = path[:len(path)-6] + "_pb2"
	}

	path = strings.Replace(path, "/", ".", -1)

	if _, ok := m.imports[path]; !ok {
		m.imports[path] = make(map[string]*ImportName)
	}

	entry := m.imports[path][name]

	if entry == nil {
		entry = &ImportName{
			name: name,
		}

		m.imports[path][name] = entry
	}

	return entry
}

func (m *PythonPkgMap) RegisterLocal(name string) {
	m.locals = append(m.locals, name)
}

func (m *PythonPkgMap) AssignAliases() {
	used := make(map[string]struct{})

	for _, local := range m.locals {
		used[local] = struct{}{}
	}

	// Sort the imports for stability
	var keys []string
	for key := range m.imports {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	for _, key := range keys {
		nameEntries := m.imports[key]

		var names []string
		for name := range nameEntries {
			names = append(names, name)
		}
		sort.Strings(names)

		for _, name := range names {
			entry := nameEntries[name]
			count := 0
			for {
				alias := name
				if count > 0 {
					alias = fmt.Sprintf("%s%d", name, count)
				}

				_, ok := used[alias]
				if !ok {
					entry.alias = alias
					used[alias] = struct{}{}
					break
				}

				count++
			}
		}
	}
}

func (m *PythonPkgMap) String() string {
	if len(m.imports) == 0 {
		return ""
	}

	m.AssignAliases()

	pylang := []string{}
	projects := []string{}

	for path, _ := range m.imports {
		if strings.HasPrefix(path, project) {
			projects = append(projects, path)
		} else {
			pylang = append(pylang, path)
		}
	}

	sort.Strings(pylang)
	sort.Strings(projects)

	hdr := NewLineWriter("    ")
	l := hdr.Line

	m.writeImports(hdr, pylang)
	if len(pylang) > 0 {
		l("")
	}

	m.writeImports(hdr, projects)
	if len(projects) > 0 {
		l("")
	}

	l("")

	return hdr.String()
}

func (m *PythonPkgMap) writeImports(
	w LineWriter,
	paths []string) {

	l := w.Line
	push := w.PushIndent
	pop := w.PopIndent

	for _, path := range paths {
		names := []string{}
		for name, _ := range m.imports[path] {
			names = append(names, name)
		}
		sort.Strings(names)

		l("from %s import (", path)
		push()
		push()

		for _, name := range names {
			entry := m.imports[path][name]
			if entry.alias == entry.name {
				l("%s,", entry.name)
			} else {
				l("%s as %s,", entry.name, entry.alias)
			}
		}

		l(")")
		pop()
		pop()
	}
}

// Is c an ASCII upper-case letter?
func isASCIIUpper(c byte) bool {
	return 'A' <= c && c <= 'Z'
}

func isScalar(fd *descriptor.FieldDescriptorProto) bool {
	switch fd.GetType() {
	case descriptor.FieldDescriptorProto_TYPE_MESSAGE,
		descriptor.FieldDescriptorProto_TYPE_GROUP:
		return false
	default:
		return true
	}
}

type Message struct {
	PkgDir  string
	PkgFile string

	FullName string

	File       *descriptor.FileDescriptorProto
	Descriptor *descriptor.DescriptorProto
}

type Descriptors struct {
	Files map[string]*descriptor.FileDescriptorProto

	// Assumption: message names are fully-qualified (starts with a '.')
	Messages map[string]*Message

	ToGenerate []*descriptor.FileDescriptorProto
}

func ParseRequest(req *plugin.CodeGeneratorRequest) (*Descriptors, error) {
	mapping := &Descriptors{
		Files:      make(map[string]*descriptor.FileDescriptorProto),
		Messages:   make(map[string]*Message),
		ToGenerate: nil,
	}

	for _, fd := range req.ProtoFile {
		mapping.Files[fd.GetName()] = fd

		pkgDir, pkgFile := path.Split(fd.GetName())
		if len(pkgDir) > 0 && pkgDir[len(pkgDir)-1] == '/' {
			pkgDir = pkgDir[:len(pkgDir)-1]
		}

		prefix := "." + fd.GetPackage() + "."
		addMessages(fd.MessageType, prefix, pkgDir, pkgFile, fd, mapping)
		addEnums(fd.EnumType, prefix, pkgDir, pkgFile, fd, mapping)

		for _, service := range fd.Service {
			for _, method := range service.Method {
				methodName := generator.CamelCase(method.GetName())
				_, ok := reservedMethodNames[methodName]
				if ok {
					return nil, fmt.Errorf(
						"Cannot use %s as method name. %s is reserved.",
						method.GetName(),
						methodName)
				}
			}
		}
	}

	for _, name := range req.FileToGenerate {
		mapping.ToGenerate = append(mapping.ToGenerate, mapping.Files[name])
	}

	return mapping, nil
}

func addMessages(messages []*descriptor.DescriptorProto, prefix, pkgDir, pkgFile string, fd *descriptor.FileDescriptorProto, descriptors *Descriptors) {
	for _, msg := range messages {
		fullName := prefix + msg.GetName()
		descriptors.Messages[fullName] = &Message{
			PkgDir:     pkgDir,
			PkgFile:    pkgFile,
			FullName:   fullName,
			File:       fd,
			Descriptor: msg,
		}
		newPrefix := prefix + msg.GetName() + "."
		addMessages(msg.NestedType, newPrefix,
			pkgDir, pkgFile, fd, descriptors)
		addEnums(msg.EnumType, newPrefix, pkgDir, pkgFile, fd, descriptors)
	}
}

func addEnums(enums []*descriptor.EnumDescriptorProto, prefix, pkgDir, pkgFile string, fd *descriptor.FileDescriptorProto, descriptors *Descriptors) {
	for _, enum := range enums {
		descriptors.Messages[prefix+enum.GetName()] = &Message{
			PkgDir:  pkgDir,
			PkgFile: pkgFile,
			File:    fd,
		}
	}
}

type LineWriter interface {
	PushIndent()
	PopIndent()
	Line(format string, values ...interface{})
	String() string
}

func NewLineWriter(indentStr string) LineWriter {
	return &lineWriter{
		indentStr: indentStr,
		indent:    0,
		content:   nil,
	}
}

type line struct {
	indentStr string
	indent    int
	format    string
	values    []interface{}
}

func (l *line) String() string {
	if l.format == "" {
		return "\n"
	}

	s := ""
	for i := 0; i < l.indent; i++ {
		s += l.indentStr
	}

	// format at the very end to allow for late binding
	s += fmt.Sprintf(l.format, l.values...) + "\n"

	return s
}

type lineWriter struct {
	indentStr string
	indent    int
	content   []*line
}

func (w *lineWriter) PushIndent() {
	w.indent += 1
}

func (w *lineWriter) PopIndent() {
	w.indent -= 1
}

func (w *lineWriter) Line(format string, values ...interface{}) {
	w.content = append(
		w.content,
		&line{
			indentStr: w.indentStr,
			indent:    w.indent,
			format:    format,
			values:    values,
		})
}

func (w *lineWriter) String() string {
	s := ""
	for _, l := range w.content {
		s += l.String()
	}

	return s
}

type pkgWriter struct {
	LineWriter

	pkgs *PythonPkgMap

	fd *descriptor.FileDescriptorProto

	descriptors *Descriptors
}

func newPkgWriter(fd *descriptor.FileDescriptorProto,
	descriptors *Descriptors) *pkgWriter {
	return &pkgWriter{
		LineWriter:  NewLineWriter("    "),
		pkgs:        NewPythonPkgMap(),
		fd:          fd,
		descriptors: descriptors,
	}
}

func (w *pkgWriter) String() string {
	// Trick tails with a little string concat
	hdr := "# @" + "generated by protoc-gen-mypy.  Do not edit!\n\n"
	return hdr + w.pkgs.String() + w.LineWriter.String()
}

func (w *pkgWriter) Name(path string, name string) *ImportName {
	return w.pkgs.From(path, name)
}

func (w *pkgWriter) RegisterLocal(name string) {
	w.pkgs.RegisterLocal(name)
}

func (w *pkgWriter) isReservedName(name string) bool {
	for _, reserved := range reservedNames {
		if name == reserved {
			return true
		}
	}
	return false
}

func (w *pkgWriter) WriteEnums(enums []*descriptor.EnumDescriptorProto, prefix string) {
	l := w.Line
	push := w.PushIndent
	pop := w.PopIndent
	name := w.Name

	text := w.Name("typing", "Text")
	for i, enumType := range enums {
		w.RegisterLocal(enumType.GetName())
		// Protobuf enums are instances of EnumWrapperType which is not a proper Python
		// enum. In order to type check properly we create a custom class for each enum with
		// the same interface as EnumWrapperType but extending int.
		qualifiedName := prefix + enumType.GetName()
		l("class %s(int):", enumType.GetName())
		push()
		l("@classmethod")
		// intentionally using int for `number` here, as we don't necessarily know if
		// the number is a valid enum
		l("def Name(cls, number: int) -> str: ...")
		l("@classmethod")
		l("def Value(cls, name: %s) -> %s: ...", text, qualifiedName)
		l("@classmethod")
		l("def keys(cls) -> %s[%s]: ...",
			name("typing", "List"), text)
		l("@classmethod")
		l("def values(cls) -> %s[%s]: ...",
			name("typing", "List"), qualifiedName)
		l("@classmethod")
		l("def items(cls) -> %s[%s[%s, %s]]: ...",
			name("typing", "List"),
			name("typing", "Tuple"),
			text, qualifiedName)
		pop()
		for _, val := range enumType.Value {
			l("%s: %s", val.GetName(), enumType.GetName())
		}
		if i < len(enums)-1 {
			l("")
		}
	}
}

func (w *pkgWriter) WriteMessages(messages []*descriptor.DescriptorProto, prefix string) {

	l := w.Line
	push := w.PushIndent
	pop := w.PopIndent
	name := w.Name

	messageClass := name("google.protobuf.message", "Message")

	for i, desc := range messages {
		clsName := desc.GetName()
		if w.isReservedName(clsName) && prefix == "" {
			clsName = "_" + clsName
		}
		w.RegisterLocal(clsName)
		qualifiedName := prefix + clsName
		l("class %s(%s):", clsName, messageClass)

		push()
		w.WriteEnums(desc.EnumType, qualifiedName+".")
		w.WriteMessages(desc.NestedType, qualifiedName+".")

		// Write types of each scalar field.
		for _, field := range desc.Field {
			if !isScalar(field) {
				continue
			}
			if field.GetLabel() == descriptor.FieldDescriptorProto_LABEL_REPEATED {
				container := name(protoContainersPkg, "RepeatedScalarFieldContainer")
				l("%s: %s[%s]", field.GetName(), container, w.pythonType(field))
			} else {
				l("%s: %s", field.GetName(), w.pythonType(field))
			}
		}

		l("")

		// Write getters for non-scalar fields. Note that we omit setters to prevent
		// people from doing proto.foo = FooProto instead of proto.foo.SetFrom(FooProto)
		for _, field := range desc.Field {
			if isScalar(field) {
				continue
			}
			l("@property")
			if field.GetLabel() == descriptor.FieldDescriptorProto_LABEL_REPEATED {
				typename := field.GetTypeName()
				if typename[0] == '.' && isASCIIUpper(typename[1]) {
					// Message defined in this file, relative path
					typename = typename[1:]
				}

				msg, ok := w.descriptors.Messages[typename]
				if ok && msg.Descriptor.Options.GetMapEntry() {
					// map generates a special Entry wrapper message.
					container := name("typing", "MutableMapping")
					l("def %s(self) -> %s[%s, %s]: ...",
						field.GetName(), container,
						w.pythonType(msg.Descriptor.Field[0]),
						w.pythonType(msg.Descriptor.Field[1]))
				} else {
					container := name(protoContainersPkg, "RepeatedCompositeFieldContainer")
					l("def %s(self) -> %s[%s]: ...", field.GetName(), container, w.pythonType(field))
				}
			} else {
				l("def %s(self) -> %s: ...", field.GetName(), w.pythonType(field))
			}
			l("")
		}

		// Write constructor type.
		l("def __init__(self,")
		push()
		// write all the required arguments first so that python doesn't get
		// mad about non-default arguments after defaults
		for _, field := range desc.Field {
			if field.GetLabel() == descriptor.FieldDescriptorProto_LABEL_REQUIRED {
				l("%s : %s,", field.GetName(), w.pythonType(field))
			}
		}
		for _, field := range desc.Field {
			if field.GetLabel() == descriptor.FieldDescriptorProto_LABEL_REQUIRED {
				continue
			}

			// Non-required arguments need to be Optional.
			optional := w.Name("typing", "Optional")
			if field.GetLabel() == descriptor.FieldDescriptorProto_LABEL_REPEATED {
				typename := field.GetTypeName()
				if len(typename) > 0 && typename[0] == '.' && isASCIIUpper(typename[1]) {
					// Message defined in this file, relative path
					typename = typename[1:]
				}

				msg, ok := w.descriptors.Messages[typename]
				if ok && msg.Descriptor.GetOptions().GetMapEntry() {
					// map generates a special Entry wrapper message.
					container := name("typing", "Mapping")
					l("%s : %s[%s[%s, %s]] = ...,",
						field.GetName(),
						optional,
						container,
						w.pythonType(msg.Descriptor.Field[0]),
						w.pythonType(msg.Descriptor.Field[1]))
				} else {
					l("%s : %s[%s[%s]] = ...,",
						field.GetName(),
						optional,
						name("typing", "Iterable"),
						w.pythonType(field))
				}
			} else {
				// Optional fields are optional.
				l("%s : %s[%s] = ...,",
					field.GetName(),
					optional,
					w.pythonType(field))
			}
		}
		l(") -> None: ...")
		pop()

		// Write standard message methods.
		l("@staticmethod")
		l("def FromString(s: bytes) -> %s: ...", qualifiedName)
		pop()
		if desc.GetName() != clsName {
			l("")
			l("%s = %s", desc.GetName(), clsName)
		}
		if i < len(messages)-1 {
			l("")
		}
	}
}

func (w *pkgWriter) pythonType(fd *descriptor.FieldDescriptorProto) interface{} {
	if fd.Options != nil {
		casttype, err := proto.GetExtension(
			fd.Options,
			mypy.E_Casttype)

		if err == nil {
			split := strings.Split(*(casttype.(*string)), ".")
			pkg := strings.Replace(split[0], "/", ".", -1)
			return w.Name(pkg, split[1])
		} else if err != proto.ErrMissingExtension {
			panic(err)
		}
	}

	switch fd.GetType() {
	case descriptor.FieldDescriptorProto_TYPE_DOUBLE, descriptor.FieldDescriptorProto_TYPE_FLOAT:
		return "float"
	case descriptor.FieldDescriptorProto_TYPE_INT64,
		descriptor.FieldDescriptorProto_TYPE_UINT64,
		descriptor.FieldDescriptorProto_TYPE_FIXED64,
		descriptor.FieldDescriptorProto_TYPE_SFIXED64,
		descriptor.FieldDescriptorProto_TYPE_SINT64,
		descriptor.FieldDescriptorProto_TYPE_INT32,
		descriptor.FieldDescriptorProto_TYPE_UINT32,
		descriptor.FieldDescriptorProto_TYPE_FIXED32,
		descriptor.FieldDescriptorProto_TYPE_SFIXED32,
		descriptor.FieldDescriptorProto_TYPE_SINT32:
		return "int"
	case descriptor.FieldDescriptorProto_TYPE_BOOL:
		return "bool"
	case descriptor.FieldDescriptorProto_TYPE_ENUM:
		return w.ImportMessage(fd)
	case descriptor.FieldDescriptorProto_TYPE_STRING:
		return w.Name("typing", "Text")
	case descriptor.FieldDescriptorProto_TYPE_BYTES:
		return "bytes"
	case descriptor.FieldDescriptorProto_TYPE_MESSAGE,
		descriptor.FieldDescriptorProto_TYPE_GROUP:
		return w.ImportMessage(fd)
	default:
		panic("Unrecognized type: " + fd.Type.String())
	}
}

func (w *pkgWriter) ImportMessage(field *descriptor.FieldDescriptorProto) interface{} {
	name := field.GetTypeName()
	if name[0] == '.' && isASCIIUpper(name[1]) {
		// Message defined in this file, relative path
		return name[1:]
	}

	message, ok := w.descriptors.Messages[name]
	if !ok {
		panic("Unable to find proto " + name)
	}
	if message.File.GetName() == w.fd.GetName() {
		// Message defined in this package, absolute path
		split := strings.Split(field.GetTypeName(), ".")
		for i, segment := range split {
			if len(segment) > 0 && isASCIIUpper(segment[0]) {
				return strings.Join(split[i:], ".")
			}
		}
		panic("Could not parse absolute name for " + field.GetTypeName())
	}

	// Otherwise, the message is not defined in this package, so we need to import.
	split := strings.Split(field.GetTypeName(), ".")
	for i, segment := range split {
		if len(segment) > 0 && isASCIIUpper(segment[0]) {
			importName := w.Name(message.File.GetName(), segment)
			remains := strings.Join(split[i+1:], ".")
			if remains == "" {
				return importName
			}
			// Handle nested message/enum - we use importName for top level
			// in case import is aliased.
			return NewNestedImport(importName, remains)
		}
	}
	panic("Could not parse local name for " + name)
}

func generateMypyStubs(
	req *plugin.CodeGeneratorRequest) *plugin.CodeGeneratorResponse {

	resp := &plugin.CodeGeneratorResponse{}

	descriptors, err := ParseRequest(req)
	if err != nil {
		errMsg := err.Error()
		resp.Error = &errMsg
		return resp
	}

	files := []*plugin.CodeGeneratorResponse_File{}
	for _, fd := range descriptors.ToGenerate {
		mypyStubs := newPkgWriter(fd, descriptors)
		mypyStubs.WriteEnums(fd.EnumType, "")
		mypyStubs.WriteMessages(fd.MessageType, "")

		pathName := strings.TrimSuffix(fd.GetName(), ".proto") + "_pb2.pyi"
		content := mypyStubs.String()
		files = append(files,
			&plugin.CodeGeneratorResponse_File{
				Name:    &pathName,
				Content: &content,
			})
	}

	resp.File = files
	return resp
}

func main() {
	req := command.Read()
	command.Write(generateMypyStubs(req))
}
