
_FUNC_RENDER_TEMPLATE = """{return_type} {func_name}({func_args})
{{
{func_body}}}
"""


class FunctionRender(object):
    def __init__(self, func_definition, func_name=None):
        self.definition = func_definition
        self.func_name = func_name
    def _get_func_name(self):
        if self.func_name:
            return self.func_name
        else:
            return self.definition.name + '_func'
    def _join_func_arg(self, arg):
        if arg.type.endswith('*'):
            return arg.type + arg.name
        else:
            return arg.type + ' ' + arg.name
    def _get_func_args(self): 
        args_string = ''
        preamble_len = (len(self.definition.return_type) 
                       + len(self._get_func_name()) + 2)
        indent_len = preamble_len
        indent_str = ' ' * indent_len
        args_string_prep = ',\n{indent}'.format(indent=indent_str)
        args_string =  args_string_prep.join(map(self._join_func_arg,
                                             self.definition.arguments))
        return args_string
    def _get_func_body(self):
        return ''
    def render(self):
        render_string = _FUNC_RENDER_TEMPLATE.format(
            return_type=self.definition.return_type,
            func_name=self._get_func_name(),
            func_args=self._get_func_args(),
            func_body=self._get_func_body())
        return render_string
    def __str__(self):
        return self.render()
 

def render_functions(functions, function_types, RenderClass):
    func_str_list = [str(RenderClass(function_types[functions[func_name]], func_name)) 
                     for func_name in functions ]
    return '\n'.join(func_str_list)



