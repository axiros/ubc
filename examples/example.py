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

        @classmethod
        def a_really_really_loooo_path_to_func(i=23, j='str'):
            '''## Some documentation
            over `multiple` lines
            - list1
            - list2
            '''
            return i


