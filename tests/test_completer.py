#!/usr/bin/env python -tt

'''
Tests for the completer

You can see the real life behaviour on the CLI like this:

    3 ~/GitHub/b2p $ cat test.sh

rl_tab_compgen () {
    echo "$COMP_WORDBREAKS" >> /tmp/wb
    cur=${COMP_WORDS[$COMP_CWORD]}
    cmd=( ${COMP_WORDS[@]} )
    last="$3"
    pos="$COMP_POINT"
    COMPREPLY=( `python -Ss "./completer.py" \
        "$CFG_DIR" "$cmd" "$cur" "$last" "$COMP_LINE" "$pos" 1 `)
}



$ source test.sh
$ xport CFG_DIR="/tmp/test_b2p_compl"
$ complete -o nosort -F rl_tab_compgen mm
$ mm fun2<tab>

The nosort option requires bash 4.4 else add a false as first arg to completer.py
'''


from setup import d_test, fn_reg
import unittest, sys, os
from functools import partial
import operator
import time

import completer
Err = completer.Err
T = completer.T

class UT(unittest.TestCase):
    def setUp(s): pass

# we use | to write the seperator, convenient
def insert_spc(s):
    return s.replace('|', T.spc)


class Tab(UT):
    ''' test tab '''
    def setUp(s):
        f = s.f = completer.Facts()
        f.cmd = 'mm'
        f.cur = ''
        f.last = 'mm'
        f.line = 'mm '
        f.d_cfg = d_test
        f.testmode = 1
        s.sep = {'sep': T.spc}
        # not seen in unittest process -> allow user to set it:
        f.term_width = int( os.environ.get('COLS'
                          , os.environ.get('COLUMNS', 80)))

    def main(s):
        s.f.line = insert_spc(s.f.line)
        s.f.pos = str(len(s.f.line)) # comes as string
        try:
            completer.main(s.f)
        except completer.ComplTestmodeExc as ex:
            return ex.args

    def c(s, send, rcv=(), exact=None, vert=False
          , exp_err=None, compl=None, dbg=None):
        if vert:
            s.f.force_vertical=True
        if dbg:
            import pdb; pdb.set_trace()
        send = 'mm ' + send
        exct = False
        if isinstance(rcv, basestring):
            rcv = (rcv,)
        s.f.line = send
        out, err = s.main()
        if exact:
            assert out.strip() == exact.strip(), '%s expected. got %s.' % (out, exact)
            return out
        if compl:
            # does every line start with it?
            for line in out.splitlines():
                if line:
                    assert line.startswith(compl)
        for v in rcv:
            s.c(v)
        if exp_err:
            s.c(exp_err[0] % exp_err[1])
        else:
            assert completer.T.func_st_err[0] not in out, 'Got unexp. error %s' % out
        return out

def vert_mark_fmt(vmarker):
    # the vertical output marker column (most left) is formatted like this
    # in the func_doc:
    # if you change there change also here:
    return '  ' + vmarker + ' ' if vmarker else ''
vmf = vert_mark_fmt

class FindFunc(Tab):
    def test_nil(s):
        s.c('', ('Foo.FooSub.subsub\n', '\nfun\n'))

    def test_nil_(s):
        s.c(' ', ('Foo.FooSub.subsub\n', '\nfun\n'))

    def test_f(s):
        s.c('f', 'fun\nfun1\nfun2')

    def test_Fo(s):
        s.c('Fo', 'Foo.FooSub.subsub\nFoo.sub', compl='Foo.')


    def test_x(s):
        s.c('x', ('Foo.FooSub.subsub\n', '\nfun\n')
                , exp_err=(Err.func_unknown, ('mm x',)))

    def test_x_(s):
        s.c('x ', ('Foo.FooSub.subsub\n', '\nfun\n')
                 , exp_err=(Err.func_unknown, ('mm x',)))

    def test_sub(s):
        s.f.match_substr = True
        s.c('sub', 'Foo.FooSub.subsub\nFoo.sub', compl='Foo.')

    def test_subsub(s):
        s.f.match_substr = True
        s.c('subsub', compl='Foo.FooSub.subsub')

    def test_subs_(s):
        s.f.match_substr = True
        s.c('subs ', ('Foo.FooSub.subsub\n', '\nfun\n')
                , exp_err=(Err.func_unknown, ('subs',)))


class Misc(Tab):
    def test_space_to_subs_match(s):
        # space -> subs match
        out = s.c(' indeed', exact='Foo.FooSub.a_very_long_function_indeed' )

class HelpSys(Tab):
    def test_modh(s):
        out = s.c('mm ??')

class HaveFunc(Tab):

    def test_fun1(s):
        s.c('fun1', exact='fun1')

    def test_sub(s):
        s.f.match_substr
        s.c('fun1', exact='fun1')

    def test_fun1_j_eq_apo_a_b(s):
        ''' no compl on spaces, that would be requiring the fake space hack'''
        res = s.c('fun1 j="a b', exact='')

    def test_fun1_j_eq_apo_a_bapo(s):
        ''' no compl on spaces, that would be requiring the fake space hack'''
        res = s.c('fun1 j="a b"', ('boolsch', 'foo', 'fl', 'fun1('))

    def test_b(s):
        s.c('fun1 j="adf" i=23 foo="bar" b', 'boolsch=[True]')


    def test_boolsch_eq(s):
        s.c('fun1 j="adf" i=23 foo="bar" boolsch=',
                vmf(T.hilite_reqv) + 'boolsch', vert=True)

    def test_val_key_compl(s):
        s.c('fun2 asdf 13', exact='13')

    def test_val_key_after_compl(s):
        s.c('fun2 asdf 13 ', T.func_st_compl[0].strip())

    def test_long(s):
        s.f.match_substr = True
        s.c('Foo.FooSub.a_very_long_function_with ',
           vmf(T.hilite_reqv) + 'even_longer_argument_i_mean_this_is_crazy=42')


    def test_fun_sub(s):
        s.f.match_substr=True
        s.c('sub', 'Foo.FooSub.subsub\nFoo.sub')

    def test_fun_subs(s):
        s.f.match_substr = True
        s.c('subs', 'Foo.FooSub.subsub')


    def test_subsub_spc_a(s):
        s.f.match_substr = True
        s.c('Foo.FooSub.subsub ', 'a="\na="[-]"')


    # dissed from here, the old tests. react if required.
    def xtest_subsub_spc_a_eq_apo(s):
        s.f.match_substr = True
        s.f.line = 'mm Foo.FooSub.subsub a="'
        out, err = s.main()
        s.c('a=\n')



    def xtest_fun_subs_spc(s):
        s.f.match_substr = True
        s.f.line = 'mm subs '
        out, err = s.main()
        s.c(completer.Err.func_unknown % 'subs')


    def xtest_fun(s):
        # we want 3 options when no space:
        s.f.line = 'mm fun'
        out, err = s.main()
        s.c('\nfun\nfun1\nfun2\n')


    def xtest_fun1(s):
        # we want 3 options when no space:
        s.f.line = 'mm fun1'
        out, err = s.main()
        assert out =='\nfun1\n'


    def xtest_fun1_1(s):
        s.f.line = 'mm fun1 j="'
        out, err = s.main()
        s.c('\nj=\n')
        assert 'fun1 doc' in out


    def xtest_fun1_boolsch_compl(s):
        s.f.line = 'mm fun1 j="sd" foo="adf" boolsch=f'
        out, err = s.main()
        s.c('\nFalse\n')


    def xtest_fun1_boolsch_compl_wrong_type(s):
        s.f.line = 'mm fun1 j="sd" foo="adf" boolsch=a'
        out, err = s.main()
        assert completer.Err.type_err % ('boolsch', 'bool') in out


    def xtest_fun1_boolsch_compl_wrong_type_1(s):
        s.f.allow_ci_bool = False
        s.f.line = 'mm fun1 j="sd" foo="adf" boolsch=t'
        out, err = s.main()
        assert completer.Err.type_err % ('boolsch', 'bool') in out


    def xtest_fun2(s):
        # we want 3 options when no space:
        s.f.line = 'mm fun1|j="afd'
        out, err = s.main()
        assert out == '\nafd\n'


    def xtest_fun3(s):
        # we want 3 options when no space:
        s.f.line = 'mm fun1|j="afd"|'
        out, err = s.main()
        #s.c('\nafd"|')


    def xtest_fun4(s):
        # we want 3 options when no space:
        s.f.line = 'mm fun1 j="afd'
        out, err = s.main()
        assert out == '\nafd\n'


    def xtest_fun5(s):
        # we want 3 options when no space:
        s.f.line = 'mm fun1|j="afd" '
        out, err = s.main()
        assert out == '\ni[=23]\nboolsch[=True]\nfoo[=bar]\nfl[=1.23]\n'


    def xtest_fun6_int(s):
        s.f.line = 'mm fun1 j="adfs" i=2'
        out, err = s.main()
        assert out == '\n23\n' # completed


    def xtest_fun6_int_no_compl(s):
        s.f.dflt_compl_nrs = False
        s.f.line = 'mm fun1 j="adfs" i=2'
        out, err = s.main()
        assert out == '\n2\n' # completed


    def xtest_fun7(s):
        s.f.line = 'mm fun1 j="adfs" i="a'
        out, err = s.main()
        s.c(completer.Err.type_err % ('i', 'int'))


    def xtest_doc_sig(s):
        s.f.line = 'mm Foo.sub s="'
        out, err = s.main()
        s.c('Some Foo method')
        assert '\ns[=str]\n' in out


    def xtest_multiblocks(s):
        s.f.line = 'mm fun1|j=23 i="3"|fl=1'
        out, err = s.main()
        assert out == '\n1.23\n'

    def xtest_sub_spc(s):
        s.f.line = 'mm sub '
        out, err = s.main()
        s.c(completer.Err.func_unknown % 'mm sub')



    def xtest_fun2_parg_n_wrong(s):
        # we want 3 options when no space:
        for e in 'mm fun2|bax=f', 'mm fun2|bax=':
            s.setUp()
            s.f.line = 'mm fun2|bax=f' # its bar not bax
            out, err = s.main()
            s.c(completer.Err.expct_other % ('bar', 'bax'))


    def xtest_fun_spc(s):
        # we want the args now:
        s.f.line = 'mm fun '
        out, err = s.main()
        s.c('\nfoo="\nfoo="[-]"')


    def xtest_fun_spc_apo(s):
        # we want the args now:
        s.f.line = 'mm fun "'
        out, err = s.main()
        assert '\nfoo=\n' in out
        assert 'some doc string' in out


    def xtest_fun12(s):
        s.f.line = 'mm fun2'
        out, err = s.main()
        assert out == '\nfun2\n'


    def xtest_fun2_spc(s):
        s.f.line = 'mm fun2 '
        out, err = s.main()
        s.c('\nbar="\nbar="[-]"')
        assert 'Fun2' in out
        assert 'i=23' in out


if __name__ == '__main__':
    unittest.main()


