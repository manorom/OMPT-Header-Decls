from __future__ import print_function
import sys
from clang import cindex

from ompt_header import parse_ompt_callbacks, parse_ompt_callback_types
from decl_print import FunctionRender, render_functions


index = cindex.Index.create()
tu = index.parse(sys.argv[1], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)


ompt_callbacks = parse_ompt_callbacks(tu)
ompt_callback_types = parse_ompt_callback_types(tu)

ompt_callback_funcs = dict((key + '_func', value) for (key, value) in 
                        ompt_callbacks.iteritems())


print(render_functions(ompt_callback_funcs,
                       ompt_callback_types,
                       FunctionRender))
