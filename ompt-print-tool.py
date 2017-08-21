#!/usr/bin/env python
from __future__ import print_function
import sys
from clang import cindex

from ompt_header import (parse_ompt_callbacks, 
                         parse_ompt_callback_types,
                         parse_ompt_enum_typedefs,
                         render_ompt_initialize_func,
                         render_ompt_finalize_func,
                         render_ompt_start_func)
from decl_print import (render_functions, 
                        FunctionRender,
                        render_enum_value_arrays)



class PrintFunctionRender(FunctionRender):
    def __init__(self, func_definition, enums_available=None, **kwargs):
        self.enums_available = enums_available if enums_available else {}
        super(PrintFunctionRender, self).__init__(func_definition, **kwargs)
    def _get_format_str_args(self):
        # a generator that yields a 2-tuple of the correct format string and
        # the correct argument for printf for every argument of the functions'
        # definitoin
        for arg in self.definition.arguments:
            # if we have an enum values array for this enum -> print that
            if arg.type in self.enums_available:
                #enum_name = self.enums_available[arg.type].type_name
                yield ('{}=%s=%d'.format(arg.name),
                       '{0}_values[{1}], {1}'.format(arg.type,
                                                     arg.name))
            # ompt_data_t * is a special case. We can simply print it value
            elif arg.type == 'ompt_data_t *':
                yield (arg.name + '=%" PRIu64 "', arg.name + '->value')
            # print all other pointers as %p
            elif arg.type.endswith('*'):
                yield (arg.name + '=%p', arg.name)
            elif arg.type == 'int':
                yield(arg.name + '=%i', arg.name)
            elif arg.type == 'unsigned int':
                yield(arg.name + '=%u', arg.name)
            # ompt_id_t is a typedef to uint64_t. We do not need an extra cast
            elif arg.type == 'ompt_id_t':
                yield(arg.name + '=%" PRIu64 "', arg.name)
            # else: simply convert arg to uint64_t and hope for the best
            else:
                yield (arg.name + '=%" PRIu64 "', '(uint64_t)'+arg.name)
    def _get_func_body(self):
        print_str = '    printf("{cbname}: {fmt_str}\\n", {fmt_args});\n'
        format_str = ', '.join([fmt for (fmt, _) in self._get_format_str_args()])
        format_args = ', '.join([fmt_arg for (_, fmt_arg) in self._get_format_str_args()])
        return print_str.format(cbname=self.func_name[:-5],
                                fmt_str=format_str,
                                fmt_args=format_args)


index = cindex.Index.create()
tu = index.parse(sys.argv[1], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

# parse macro to get all callbacks + their types
ompt_callbacks = parse_ompt_callbacks(tu)

# parse all ompt func pointer typedefs
ompt_callback_types = parse_ompt_callback_types(tu)

# parse all enums
all_ompt_enums = parse_ompt_enum_typedefs(tu)

# find all enums in arguments
used_ompt_enums = {}
for cbt in ompt_callback_types:
    for arg in ompt_callback_types[cbt].arguments:
        if arg.type in all_ompt_enums and arg.type not in used_ompt_enums:
            used_ompt_enums[arg.type] = all_ompt_enums[arg.type]


# set name of callback functions
ompt_callback_funcs = dict((key + '_func', ompt_callback_types[value])
                           for (key, value) in ompt_callbacks.iteritems())

ompt_callback_name_funcs = dict((key + '_func', key) for key in ompt_callbacks)

# print everything
print('#include <inttypes.h>')
print('#include <stdio.h>')
print('#include <ompt.h>\n\n')

print(render_enum_value_arrays(used_ompt_enums))

print('')

print(render_functions(ompt_callback_funcs,
                       PrintFunctionRender,
                       enums_available=used_ompt_enums))

print(render_ompt_initialize_func(ompt_callback_name_funcs))

print(render_ompt_finalize_func())
print(render_ompt_start_func())
