#!/usr/bin/env python -tt
import sys, os
d_test = '/tmp/test_b2p_compl'
fn_reg = d_test + '/var/funcs/mm/defs.py'

os.system('mkdir -p "%s"' % d_test) if not os.path.exists(d_test) else 0
script = 'c.py'
pth = os.path.abspath(__file__).rsplit('/', 2)[0]
sys.path.insert(0, pth)
sys.path.insert(0, d_test)

def create_mod(name, cont):
    with open(d_test + '/' + name + '.py', 'w') as fd:
        fd.write(cont)

create_mod('mm', """
'''
# MyMod
- does this
- and that
'''
import json



def fun(foo):
    '''some doc string
    stuf
    '''

def intg(i=3): pass

def fun1(j, i=23, foo="bar", boolsch=True, fl=1.23):
    '''fun1 doc
    line2
    '''
    return bar, i

def fun2(bar, i=23):
    '''# Fun2
    ## does
    - this
    - that
    '''
    return bar, i

class Foo:
    '''Foo Sub'''
    def sub(s='str'):
        '''Some Foo method'''
        return s
    class FooSub:
        def subsub(a): pass
        def a_very_long_function_indeed(long_arg1='fooobar_default'
                , loooongarg2=True
                , even_longer_argument_i_mean_this_is_crazy=42
                ):
            '''And quite fittingly a suuuuperlong docstring
            which extends
            over a few
            lines and such'''
""")

