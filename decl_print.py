
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
            return self.definition.name
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
        return _FUNC_RENDER_TEMPLATE.format(
            return_type=self.definition.return_type,
            func_name=self._get_func_name(),
            func_args=self._get_func_args(),
            func_body=self._get_func_body())
    def __str__(self):
        return self.render()


_ENUM_ARRAY_RENDER_TEMPLATE = """static const char* {name}[] = {{
    {values}
}};
"""


class EnumValuesArrayRender(object):
    def __init__(self, enum_definition, array_name=None):
        self.definition = enum_definition
        self.array_name = array_name
    def _render_values(self):
        cur_array_index = 0
        for (enum_name, enum_value) in self.definition.get_sequential():
            while enum_value > cur_array_index:
                yield 'NULL,'
                cur_array_index += 1
            yield '"{}",'.format(enum_name)
            cur_array_index += 1
    def render(self):
        name = self.array_name
        if not name:
            name =  self.definition.type_name + '_values'
        array_values = self._render_values()
        array_values_str = '\n    '.join(array_values)
        return _ENUM_ARRAY_RENDER_TEMPLATE.format(name=name,
                                                  values=array_values_str)
    def __str__(self):
        return self.render()


def render_enum_value_arrays(enums):
    enum_str_list = [str(EnumValuesArrayRender(enums[enum_name]))
                     for enum_name in enums]
    return '\n'.join(enum_str_list)

def render_functions(functions, RenderClass=FunctionRender, **kwargs):
    func_str_list = [str(RenderClass(functions[func_name],
                                     func_name=func_name, **kwargs)) 
                     for func_name in functions ]
    return '\n'.join(func_str_list)

