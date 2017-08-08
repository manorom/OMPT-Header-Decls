#!/usr/bin/env python
from __future__ import print_function
import sys
from clang import cindex

from ompt_header import (parse_ompt_callbacks, 
                         parse_ompt_callback_types, 
                         render_ompt_initialize_func,
                         render_ompt_finalize_func,
                         render_ompt_start_func)
from decl_print import render_functions


index = cindex.Index.create()
tu = index.parse(sys.argv[1], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)


ompt_callbacks = parse_ompt_callbacks(tu)
ompt_callback_types = parse_ompt_callback_types(tu)


ompt_callback_funcs = dict((key + '_func', ompt_callback_types[value])
                           for (key, value) in ompt_callbacks.iteritems())


print('#include <ompt.h>\n\n')

print(render_functions(ompt_callback_funcs))


ompt_callback_name_funcs = dict((key + '_func', key) for key in ompt_callbacks)

print(render_ompt_initialize_func(ompt_callback_name_funcs))


print(render_ompt_finalize_func())
print(render_ompt_start_func())
