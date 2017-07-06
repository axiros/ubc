#!/usr/bin/env python -tt
from setup import d_test, fn_reg
import unittest, sys, os
from functools import partial
import operator
import time

import indexer

class T(unittest.TestCase):
    def setUp(s): pass


class PM(T):
    ''' test parse mode'''
    def setUp(s):
        s.f = indexer.Facts()
        s.f.depth = 1
        s.f.cdepth = 2
        s.f.d_cfg = d_test
        s.f.modn = 'mm'

    def test_index(s):
        indexer.main(s.f)
        # result is here:
        m = {}
        execfile(fn_reg, m)
        funcs = ['Foo.sub', 'Foo.FooSub.subsub', 'fun1', 'fun2']
        for f in funcs:
            assert f in m['funcs'] and f in m['reg'].keys()
        for f in funcs:
            for k in 'arg_keys', 'args', 'doc', 'pos_args':
                assert k in m['reg'][f]
        print('path', fn_reg)


if __name__ == '__main__':
    # tests/test_pycond.py PyCon.test_auto_brackets
    unittest.main()


