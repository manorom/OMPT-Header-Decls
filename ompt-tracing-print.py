#!/usr/bin/env python
from __future__ import print_function
import sys
from collections import namedtuple
from clang import cindex

from ompt_header import (parse_ompt_callbacks,
                         parse_ompt_record_types,
                         parse_ompt_record_ompt_union,
                         parse_ompt_enum_typedefs)

from decl_print import _FUNC_RENDER_TEMPLATE, render_enum_value_arrays

index = cindex.Index.create()
tu = index.parse(sys.argv[1],
    options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

ompt_callbacks = parse_ompt_callbacks(tu)
ompt_record_types = parse_ompt_record_types(tu)
ompt_record_union = parse_ompt_record_ompt_union(tu)


class StructPrintFunctionRender(object):
    def __init__(self, struct_definition, func_name, callback_name=None,
                 enums_available=None):
        self.struct_definition = struct_definition
        self.func_name = func_name
        self.callback_name = callback_name if callback_name else ''
        self.enums_available = enums_available if enums_available else set()
        self.return_type = 'inline static void'
    def _get_func_args(self):
        #indent_str = '\n' + ' ' * (len(self.return_type) + 1 +
        #                           len(self.func_name) + 1)
        #return indent_str.join([ 'ompt_id_t thread_id,',
        #                         'int device_num',
        #                         '{} *record'.format(
        #                                  self.struct_definition.type_name)])
        return 'ompt_id_t thread_id, int device_num, {} *record'.format(
            self.struct_definition.type_name)
    def _get_format_str_args(self):
        # a generator that yields a 2-tuple of the correct format string and
        # the correct argument for printf for every field of the struct
        for field in self.struct_definition.fields:
            # if we have an enum values array for this enum -> print that
            if field.field_type in self.enums_available:
                #enum_name = self.enums_available[arg.type].type_name
                yield ('{}=%s=%d'.format(field.field_name),
                       '{0}_values[record->{1}], record->{1}'.format(field.field_type,
                                                     field.field_name))
            # if we have an enum values array for this enum -> print that
            # ompt_data_t * is a special case. We can simply print it value
            elif field.field_type == 'ompt_data_t *':
                yield (field.field_name + '=%" PRIu64 "',
                       'record->' + field.field_name + '->value')
            # print all other pointers as %p
            elif field.field_type.endswith('*'):
                yield (field.field_name + '=%p',
                       'record->' + field.field_name)
            elif field.field_type == 'int':
                yield(field.field_name + '=%i',
                      'record->' + field.field_name)
            elif field.field_type == 'unsigned int':
                yield(field.field_name + '=%u',
                      'record->' + field.field_name)
            # ompt_id_t is a typedef to uint64_t. We do not need an extra cast
            elif field.field_type == 'ompt_id_t':
                yield(field.field_name + '=%" PRIu64 "',
                      'record->' + field.field_name)
            # else: simply convert arg to uint64_t and hope for the best
            else:
                yield (field.field_name + '=%" PRIu64 "',
                       '(uint64_t)'+'record->' +field.field_name)
    def _get_func_body(self):
        print_func_str = '    printf("D%i-%" PRIu64 ": {}: {}\\n", device_num, thread_id, {});\n'
        format_string = ', '.join(map(lambda x: x[0], self._get_format_str_args()))
        format_args = ', '.join(map(lambda x: x[1], self._get_format_str_args()))
        return print_func_str.format(self.callback_name,
                                     format_string,
                                     format_args)
    def __str__(self):
        return self.render()
    def render(self):
       return _FUNC_RENDER_TEMPLATE.format(
            return_type=self.return_type,
            func_name=self.func_name,
            func_args=self._get_func_args(),
            func_body=self._get_func_body())


_DISPATCH_FUNC_TEMPLATE = """\
void dispatch_trace_record(int device_num,
                           ompt_record_ompt_t *trace_record)
{{
    switch(trace_record->type)
    {{
{body}
    }}
}}
"""

_SWITCH_STMNT_TEMPLATE = """\
        case {ident}:
            {func_name}(trace_record->thread_id, device_num, &trace_record->record.{record_name});
            break;\
"""

def render_dispatch_function(callbacks_records):
    case_list = []
    for cb in callbacks_records:
        case_list.append(_SWITCH_STMNT_TEMPLATE.format(
            ident=cb,
            func_name=cb.replace('ompt_', 'on_record_'),
            record_name=callbacks_records[cb][1]))
    return _DISPATCH_FUNC_TEMPLATE.format(
            body='\n'.join(case_list))


def map_callback_types_to_records(callbacks, record_union, record_types):
    callback_type_record_map = {}
    record_union_type_map = dict((k,v) for (v,k) in record_union)
    for record_type_name in record_union_type_map:
        cb_type_name = record_type_name.replace('ompt_record_', 'ompt_callback_')
        if cb_type_name in callbacks.values():
            callback_type_record_map[cb_type_name] = (record_types[record_type_name],
                                                      record_union_type_map[record_type_name])
        else:
            print('//Could not find callback type for record type {}'.format(
                  record_type_name),
                  file=sys.stderr)
    callback_record_map = {}
    for cb in callbacks:
        if (callbacks[cb] in callback_type_record_map and
                not cb.startswith('ompt_callback_target')):
            callback_record_map[cb] = callback_type_record_map[callbacks[cb]]
    return callback_record_map


ompt_callbacks_records = map_callback_types_to_records(ompt_callbacks,
                                                       ompt_record_union,
                                                       ompt_record_types)

# parse all enums
all_ompt_enums = parse_ompt_enum_typedefs(tu)
used_ompt_enums = {}
for cbt in ompt_callbacks_records:
    for field in ompt_callbacks_records[cbt][0].fields:
        if (field.field_type in all_ompt_enums and
                field.field_type not in used_ompt_enums and
                all_ompt_enums[field.field_type].value_range <= 64):
                used_ompt_enums[field.field_type] = \
                    all_ompt_enums[field.field_type]


print('#include <stdio.h>')
print('#include <inttypes.h>')
print('#include <ompt.h>')
print('\n')

print(render_enum_value_arrays(used_ompt_enums))

print('')

for cb in ompt_callbacks_records:
    print(StructPrintFunctionRender(ompt_callbacks_records[cb][0],
                                    cb.replace('ompt_', 'on_record_'),
                                    cb, used_ompt_enums))

print('')

print(render_dispatch_function(ompt_callbacks_records))
