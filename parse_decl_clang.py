from collections import namedtuple
from clang import cindex


FunctionArgs = namedtuple('FunctionArgs', ['name', 'type'])


class FunctionDefinition(object):
    def __init__(self, name, return_type, arguments):
        self.name = name
        self.return_type = return_type
        self.arguments = arguments


def is_func_pointer_typedef(cursor):
    pointee = None
    if hasattr(cursor.underlying_typedef_type, 'get_pointee'):
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

