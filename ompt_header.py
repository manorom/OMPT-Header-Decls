from clang import cindex

from parse_decl_clang import (is_func_pointer_typedef,
                              parse_func_pointer_typedef,
                              FunctionDefinition,
                              FunctionArgs,
                              is_enum_typedef,
                              parse_enum_typedef,
                              is_struct_typedef,
                              parse_struct_typedef)
from decl_print import FunctionRender

def parse_ompt_callback_macro(cursor):
    ompt_callback_types = {}
    macro_tokens = cursor.get_tokens()
    relevant_tokens = iter(filter(lambda x: x.kind == cindex.TokenKind.IDENTIFIER,
                                  macro_tokens))
    for t in relevant_tokens:
        if t.spelling == 'FOREACH_OMPT_EVENT':
            continue
        if t.spelling == 'macro':
            continue
        callback_name = t.spelling
        callback_type = next(relevant_tokens).spelling
        ompt_callback_types[callback_name] = callback_type
    return ompt_callback_types


def parse_ompt_callbacks(tu):
    for c in tu.cursor.get_children():
        if (c.kind is cindex.CursorKind.MACRO_DEFINITION
                and c.spelling == 'FOREACH_OMPT_EVENT'):
            return parse_ompt_callback_macro(c)


def parse_ompt_callback_types(tu):
    ompt_callback_types = {}
    for c in tu.cursor.get_children():
        if (c.kind is cindex.CursorKind.TYPEDEF_DECL
                and c.spelling.startswith('ompt_callback_')
                and c.spelling != 'ompt_callback_t'
                and is_func_pointer_typedef(c)):
            ompt_callback_types[c.spelling] = parse_func_pointer_typedef(c)
    return ompt_callback_types


def parse_ompt_enum_typedefs(tu):
    ompt_enum_types = {}
    for c in tu.cursor.get_children():
        if (c.kind is cindex.CursorKind.TYPEDEF_DECL
            and c.spelling.startswith('ompt_')
            and is_enum_typedef(c)):
            ompt_enum_types[c.spelling] = parse_enum_typedef(c)
    return ompt_enum_types


def parse_ompt_record_types(tu):
    record_types = {}
    for ch in tu.cursor.get_children():
        if (ch.kind is cindex.CursorKind.TYPEDEF_DECL and
                is_struct_typedef(ch) and
                ch.spelling.startswith('ompt_record_') and
                ch.spelling != 'ompt_record_type_t' and
                ch.spelling != 'ompt_record_ompt_t'):
            record_types[ch.spelling] = (parse_struct_typedef(ch))
    return record_types


def _parse_record_union(cursor):
    union_members = []
    for ch in cursor.get_children():
        if ch.kind is cindex.CursorKind.FIELD_DECL:
            union_members.append((ch.spelling, ch.type.spelling))
    return union_members


def parse_ompt_record_ompt_union(tu):
    for cursor in tu.cursor.get_children():
        if cursor.spelling == 'ompt_record_ompt_t':
            for ch in next(cursor.get_children()).get_children():
                if ch.spelling == 'record':
                    return _parse_record_union(ch.type.get_declaration())


class OMPTInitializeFunctionRender(FunctionRender):
    def __init__(self, ompt_callbacks, add_entry_points=None):
        ompt_initialize_args = [FunctionArgs(type='ompt_function_lookup_t',
                                             name='lookup'),
                                FunctionArgs(type='struct ompt_fns_t *',
                                             name='fns')]
        func_def = FunctionDefinition('ompt_initialize',
                                      'int',
                                      ompt_initialize_args)
        super(OMPTInitializeFunctionRender, self).__init__(func_def,
                                                           'ompt_initialize')
        self.ompt_callbacks = ompt_callbacks
        self.add_entry_points = add_entry_points
        if not self.add_entry_points:
            self.add_entry_points = []

    def _get_func_body(self):
        s1 = '    ompt_set_callback_t ompt_set_callback = (ompt_set_callback_t) lookup("ompt_set_callback");\n'

        callback_registration_str = ['ompt_set_callback({cbname}, (ompt_callback_t) &{cbfunc});'.format(cbname=self.ompt_callbacks[name],
                                                                                                        cbfunc=name)
                                     for name in self.ompt_callbacks]
        s2 = '\n    ' + '\n    '.join(callback_registration_str)
        s3 = '\n\n    return 1;\n'
        return s1 + s2 + s3


def render_ompt_initialize_func(ompt_callbacks, add_entry_points=None):
   return OMPTInitializeFunctionRender(ompt_callbacks,
                                       add_entry_points)


def render_ompt_finalize_func():
    return """void ompt_finalize(struct ompt_fns_t *fns)
{
}
"""


def render_ompt_start_func():
    return """struct ompt_fns_t fns = {ompt_initialize, ompt_finalize};

ompt_fns_t *ompt_start_tool(unsigned int omp_version, const char *runtime_version)
{
    return &fns;
}"""

