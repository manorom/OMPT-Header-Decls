from clang import cindex

from parse_decl_clang import (is_func_pointer_typedef,
                              parse_func_pointer_typedef)


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
