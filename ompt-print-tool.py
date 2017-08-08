#!/usr/bin/env python
from __future__ import print_function
import sys
from clang import cindex

from ompt_header import (parse_ompt_callbacks, 
                         parse_ompt_callback_types, 
                         render_ompt_initialize_func,
                         render_ompt_finalize_func,
                         render_ompt_start_func)
from decl_print import render_functions, FunctionRender



class PrintFunctionRender(FunctionRender):
    def _get_format_str_type(self, arg_type):
        if arg_type == 'ompt_data_t *':
            return '%" PRIu64 "'
        if arg_type.endswith('*'):
            return '%p'
        if arg_type == 'int':
            return '%i'
        if arg_type == 'unsigned int':
            return '%u'
        return '%" PRIu64 "'
    def _get_func_body(self):
        func_body = '    printf("{fmt_str}\\n"{fmt_args});\n'

        format_string = self.func_name[:-5] + ': '
        format_string += ' '.join([ '{}={}'.format(arg.name,
                                                  self._get_format_str_type(arg.type))
                                    for arg in self.definition.arguments])
        printf_args = ''
        for arg in self.definition.arguments:
            if arg.type == 'ompt_data_t *':
                printf_args += ', {}->value'.format(arg.name)
            else:
                format_str = self._get_format_str_type(arg.type)
                if (format_str == '%\" PRIu64 \"' 
                    and not arg.type.endswith('id_t')
                    and not arg.type == 'uint64_t'):
                    printf_args += ', (uint64_t){}'.format(arg.name)
                else:
                    printf_args +=', {}'.format(arg.name)
        return func_body.format(fmt_str=format_string, fmt_args=printf_args)


index = cindex.Index.create()
tu = index.parse(sys.argv[1], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)


ompt_callbacks = parse_ompt_callbacks(tu)
ompt_callback_types = parse_ompt_callback_types(tu)

ompt_callback_funcs = dict((key + '_func', ompt_callback_types[value])
                           for (key, value) in ompt_callbacks.iteritems())

ompt_callback_name_funcs = dict((key + '_func', key) for key in ompt_callbacks)


print('#include <inttypes.h>')
print('#include <stdio.h>')
print('#include <ompt.h>\n\n')


print(render_functions(ompt_callback_funcs,
                       PrintFunctionRender))

print(render_ompt_initialize_func(ompt_callback_name_funcs))

print(render_ompt_finalize_func())
print(render_ompt_start_func())
