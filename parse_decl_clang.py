from collections import namedtuple
from clang import cindex


FunctionArgs = namedtuple('FunctionArgs', ['name', 'type'])


class EnumDefinition(object):
    def __init__(self, type_name, values=None):
        self.type_name = type_name
        self.values = values if values else {}
    def add_entry(self, key, value):
        self.values[key] = value
    def get_sequential(self):
        k_v_list = list(self.values.items())
        k_v_list.sort(key=lambda x: x[1])
        for entry in k_v_list:
            yield entry
    def __iter__(self):
        return self.get_sequential()
    def __len__(self):
        return len(self.values)
    def __str__(self):
        return 'EnumDefinition \'{}\': {}'.format(self.type_name,
                                                  list(self.get_sequential()))


class FunctionDefinition(object):
    def __init__(self, name, return_type, arguments):
        self.name = name
        self.return_type = return_type
        self.arguments = arguments


def is_func_pointer_typedef(cursor):
    pointee = None
    if cursor.underlying_typedef_type.kind is cindex.TypeKind.POINTER:
        pointee = cursor.underlying_typedef_type.get_pointee()    

    if pointee:
        pointee_kind = pointee.get_canonical().kind
        return pointee_kind == cindex.TypeKind.FUNCTIONPROTO
    return False


def parse_func_pointer_typedef(cursor):
    arguments = []
    return_type = 'void'
    for ch in cursor.get_children():
        if ch.kind is cindex.CursorKind.PARM_DECL:
            arg_type = ch.type.spelling
            arg = FunctionArgs(type=arg_type, name=ch.spelling)
            arguments.append(arg)
        elif ch.kind is cindex.CursorKind.TYPE_REF:
            return_type = ch.spelling
    return FunctionDefinition(cursor.spelling, return_type, arguments)


def is_enum_typedef(cursor):
    if cursor.underlying_typedef_type.kind is cindex.TypeKind.ELABORATED:
        try:
            decl = next(cursor.get_children()).kind
            if decl is cindex.CursorKind.ENUM_DECL:
                return True
        except StopIteration:
            return False
    return False


def parse_enum(cursor):
    enum = EnumDefinition(cursor.spelling)
    for ch in cursor.get_children():
        enum.add_entry(ch.spelling, ch.enum_value)
    return enum

def parse_enum_typedef(cursor):
    enum = parse_enum(next(cursor.get_children()))
    enum.type_name = cursor.spelling
    return enum
