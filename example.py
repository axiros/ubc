'''
Completion sample module

'''


def func_module_level(i, a='foo'):
    'some docu'
    return i * a


class ModClass:
    ''' some inner namespace class'''
    @classmethod
    def class_level_func(cls, boolean=True):
        return boolean

    class NestedClass:
        ''' some inner namespace class'''
        @classmethod
        def class_level_func(cls, a_str='foo', boolean=True):
            return boolean or a_str



