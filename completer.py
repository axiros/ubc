#!/usr/bin/env python -Ss
# coding: utf-8
'''

# Tab Completer

Started at each tab key for a registered cmd prefix.

Must print to stdout a list of valid completions, which bash reduces to the
longest common match, then prints on the the cli at current cursor position
where <tab> is pressed.

If <tab> is pressed 2 times the full list is shown before completion.

We make heavy use of that.

See README.md


# DEV NOTES

Few helpers for reading the code:
    f, s: (single) instances of Facts(outside infos) and State - those are
          everywhere. Could have used classes but maybe this sometimes runs
          centrally, stateful and completes many remote clients, lets see.
    T: The tags class, just a namespace for characters to format

Start by reading main().

Phases:
    1. try find function. Exit if not unique
    2. go through all completed arg/val blocks, register entered args, report
       errors
    3. check the last fragment, where <tab> was pressed.
       These leads to calling one of the 4 different exit functions, i.e.
       exit_complete_singe_key

A large part is formatting the output for dbl tab, no need to understand for the major flow.
'''
import sys, os, shlex

# make py2 >> 3?
# no, can't, lets do it properly this one time.
#reload(sys); sys.setdefaultencoding('utf-8')

# why? because if this should run on py3 we have to stuff our code full of
# encode/decode statements *anways*.
# (why do people accept this sh... as an "improvement")
# long story short: should you have any problem with encoding errors with your
# overwritten tags and markers: use py2 which will live forever and uncomment
# the line above - and all on that front will be fine.
# Guaranteed.
# Btw: U want py2 anyway since this starts 2 times faster and this program
# starts often... Its just your tab completer, in the end :-)

# ----------------------------------------------------------------------- Tools
PY2 = sys.version_info[0] == 2
is_str = lambda s: isinstance(s, basestring if PY2 else (bytes, str))
debug = 1 #False

# debug:
def l(*m):
    with open('/tmp/compl_log', 'a') as fd:
        fd.write(' '.join([str(s) for s in m]))
        fd.write('\n')


class Repr: # Debug Helper.
    def _pub_args(s):
        ''' all config attributes of a class. no functions, no internals'''
        els = [(n, getattr(s, n)) for n in dir(s) if not n.startswith('_')]
        return [(k, v) for k, v in els if not hasattr(v, 'code')]


    def __str__(s):
        d = dict([(k, v) for k, v in self._pub_args()])
        import pprint
        return pprint.pformat(d)



# ------------------------------------------------------------------CLI Parsing
class ComplTestmodeExc(Exception): 'In testmode we raise instead of sys.exit'
class T:
    'Tags Namespace'
    # \xc2\xa0 looks like a space. is no space (non breaking space)
    spc                = '\xc2\xa0'
    #spc               = '\xE2\x80\x94' # debugging one (visual)
    doc_start          = ' '
    doc_end            = ' '
    warn_pre           = ''
    warn_post          = ''
    no_dflt            = 'n.d.' # set by the indexer !
    hilite_req         = '△'
    hilite_reqv        = '▷'
    hilite_have_key    = '▲'
    hilite_have_keyv   = '▶' # vertical sig version
    hilite_norm        = '─'
    hilite_norm_compl  = '━'
    hilite_normv       = '⎸'
    hilite_have        = '═'
    hilite_havev       = '▌'
    hilite_err_key     = '!'
    hilite_err_keyv    = '!'
    func_st_norm_s     = ' »,« ' # left and right, split by , (to allow via env)
    func_st_compl_s    = '√ , √'
    func_st_err_s      = '! , !'
    func_st_norm       = func_st_norm_s.split(',')
    func_st_err        = func_st_err_s.split(',')
    func_st_compl      = func_st_compl_s.split(',')


env_prefix = 'ubc_' # see __init__

class Facts(Repr):
    '''Namespace for Infos from Outside
    (i.e. env, indexer, testprog, bash complete function...)
    '''
    # We do instantiate, for later stateful mode but we never change attrs
    # after init.
    line            = None # as currently on the screen. maybe with seps
    cmd             = None # the principal command. 'hg' in 'hg cl<tab>'
    last            = None # unused
    d_cfg           = None # where to load the index
    testmode        = None # no sys.exit but raise result
    # you can switch= this on per command like 'cmd  subs<tab>' (add. space)
    match_substr    = 'on_demand' # allow to enter func names not from start
    allow_ci_bool   = True # allow to enter bools case insensitive
    dflt_compl      = True # complete started defaults
    dflt_compl_nrs  = True # so this also for numbers
    have_no_sort    = True # switch false if can't do (bash set -o no_sort)
    force_vertical  = False
    doc_show        = True
    sig_show        = True
    sig_rpl_dflts   = True # when we have values we put into sigline
    term_width      = 80   # all will be goin south if we don't have this right


    def setup(f):
        '''set all keys starting with prefix either into facts f or tags T'''
        env, lp = os.environ, len(env_prefix)
        # poor man's config engine. we have not much time...
        ck = [(k[lp:], env[k]) for k in env.keys() if k.startswith(env_prefix)]
        [setattr((f if hasattr(f, k) else T), k, v) for k, v in ck]

        f.term_width = int(f.term_width)
        if not f.d_cfg:
            raise Exception('have no config dir, set $%sd_cfg' % env_prefix)

        # indexer infos are also from outside, came earlier but still belong
        # here:
        f.cmd = f.line.split(' ', 1)[0]

        m = f.load_file('defs.py')
        f.funcs, f.reg = m['funcs'], m['reg']


    def load_file(f, fn):
        m, fn = {}, f.d_cfg + '/var/funcs/%s/%s' % (f.cmd, fn)
        #if not os.path.exists(fn):
        try:
            execfile(fn, m)
            return m
        except Exception as ex:
            raise Exception('Error loading %s - did indexer run? %s'% (fn, ex))


class State(Repr):
    'Namespace for internal parsing state. We keep our progress here'
    #TODO: document all used attrs
    # attrs change all the time
    line        = None # line w/o the command
    out         = ''    # what we'll return to bash.complete
    val_compl   = ''    # did we find a completion for a value? e.g. t->True
    args_left   = None  # args which are in the sig but not yet entered
                        # initted by args in reg[<func>] in defs.py

    reg        = None # set as soon we have the function
    res        = None
    err        = ''
    sh_compl   = False # the list of completion options we'll return
    func_st    = T.func_st_norm
    err_key    = None
    doc_built  = False
    hilite     = None # keys to hilite in status line
    help_mode  = None # does the user want help ?
    help_shown = False


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -Functions. Easy.

def match_entered_func(f, s, all_=None):
    '''s.func as entered. We build s.func_matches and reduce s.func to matching
    supplying all_ this is also used to match the mods / funcs in doc.py
    '''
    all_ = f.funcs if all_ is None else all_
    def get_matches(func, s=s, f=f):
        funcs = all_
        if not func:
            return all_
        matches = [fn for fn in funcs if fn.startswith(func)]
        if not matches:
            # func given but does not match. substring match enabled?
            if s.match_substr:
                matches = [fn for fn in funcs if func in fn]
        return matches

    matches = all_ # when s.func is empty
    while s.func:
        matches = get_matches(s.func)
        if matches:
            break
        s.func = s.func[:-1]
    # def fun, fun1. -> fun<tab> shows the 2, 'fun '<tab> only fun:
    if f.line.split(' ', 1)[1].startswith(s.func + ' ') and s.func in matches:
        matches = [s.func]
    s.func_matches = matches






# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -Arguments. Hard.
dflt = lambda s, key: s.reg['args'][key]

def scan_blocks(f, s):
    #import pdb; pdb.set_trace()
    sl = s.line.replace(T.spc, ' ')
    for s.apo_miss in '', '"', "'":
        try:
            s.blocks = shlex.split(sl + s.apo_miss)
            break
        except ValueError:
            continue

    # now we validate and register all blocks. On errors we dispaly help
    # else we complete s.to_complete:
    s.kvs_seen = {} # found in blocks
    # first block is the function itself.
    s.blocks.pop(0)

    # the last block is specially treated, searched for completion options.
    # IF we don't have a last block (i.e. only funcname<tab>,
    # we insert an empty one:
    if not s.blocks:
        s.blocks.append('')
    else:
        # on the opposite, if the last block is complete (i.e. ends with a
        # space, i.e. does not need to be completed anymore)
        # we also insert an empty last block:
        if not s.apo_miss:
            if f.line[-1] in " '\"":
                s.blocks.append('')

    s.last_block = s.blocks.pop()
    # ok lets start. first we copy the args, sinc we're going to pop them empty
    # during block traversal (and we need them complete for the sig docu)
    s.args_left = dict(s.reg['args'])
    s.pos_args_left = list(s.reg['pos_args'])
    try:
        while s.blocks:
            validate_and_register_block(f, s)

        complete_last_fragment(f, s)
    except Err as ex:
        l('exception')
        s.err = str(ex)
        sys_exit(f, s)


class Err(Exception):
    'block scanning exceptions'
    expct_other  = '"%s": expected "%s"'
    req_prm_name = '"%s": requiring parameter name'
    unknown      = '"%s": unknown'
    type_err     = '"%s": expected %s type'
    func_unknown = '"%s" function unknown'


# ------------------- The already entered blocks (e.g. 'a=b' in mm a=b c=<tab>'
def validate_and_register_block(f, s):
    '''we have one single key value or value only block here
    block must be complete, last one is specially checked afterwards
    '''
    block = s.blocks.pop(0)
    key, val = (block.split('=', 1)) if '=' in block else (None, block)
    pas = s.pos_args_left
    if pas:
        pa = pas.pop(0)
        if key:
            if not key == pa:
                s.err_key = pa
                raise Err(Err.expct_other % (key, pa))
        else:
            key = pa
    if not key:
        # must have pos arg then:
        raise Err(Err.req_prm_name % val)
    if not key in s.args_left:
        raise Err(Err.unknown % key)
    validate_type_of_val_vs_dflt(f, s, key, val)
    s.kvs_seen[key] = val # used to replace dflts in sigline later
    sal = s.args_left
    sal.pop(key)
    if len(sal) == 1:
        s.pos_args_left.append(sal.keys()[0])


# ------------------------------------- The pending one, just left of the <tab>
def complete_last_fragment(f, s):
    ''' we have all params registered. lets see where we are
    note: completion returns can only start from these chars: = "'
    (point of no return)
    '''
    block = s.last_block
    # in contrast to block parsing if a = is missing we are in key not val
    key, val = (block.split('=', 1)) if '=' in block else (block, None)

    pas = s.pos_args_left
    if s.apo_miss:
        # we are in a an unclosed apostr. block:
        if val is None:
            # no = -> key MUST be positional:
            if not pas:
                raise Err(Err.req_prm_name % 'this')
            key, val = pas[0], key

    if pas:
        pa = pas.pop(0)
        if val is not None:
            if key != pa:
                s.err_key = pa
                raise Err(Err.expct_other % (pa, key))
            else:
                exit_compl_single_val(f, s, pa, val)
        else:
            # complete it:
            if pa.startswith(key):
                exit_compl_single_key(f, s, pa)
            exit_compl_single_val(f, s, pa, key)

    # multiple(?) named args:
    args = s.args_left
    if not args:
        s.func_st = T.func_st_compl
        func_doc(f, s)
        #s.sh_compl.append('complete')
        sys_exit(f, s)

    if val is not None:
         if not key in args:
             raise Err(Err.unknown % key)
         exit_compl_single_val(f, s, key, val)

    key_was = key
    while 1:
        key_matches = [k for k in args if k.startswith(key)]
        if key_matches:
            break
        key = key[:-1]
    if len(key_matches) == 1:
        exit_compl_single_key(f, s, key_matches[0])

    if key_was and not key:
        # entered stuff which cannot be reduced to set of completable keys:
        s.err = Err.req_prm_name % key_was
        s.hilite = dict([(k, ulen(k)) for k in key_matches])
        sys_exit(f, s)

    exit_compl_multi_key(f, s, key_matches)


def validate_type_of_val_vs_dflt(f, s, key, val):
    '''verify if the entered value is castable into the default type'''
    d = dflt(s, key)
    if d in (True, False) and val:
        for dd in 'True', 'False':
            dd, v = (dd.lower(), val.lower()) if f.allow_ci_bool else (dd, val)
            if dd.startswith(v):
                return dd.capitalize()
        s.err_key = key
        raise Err(Err.type_err % (key, type(True).__name__))

    t = type(d)
    try:
        t(val)
        return d # returning it. safes another lookup
    except:
        s.err_key = key
        raise Err(Err.type_err % (key, t.__name__))


# ---------------------------- Assembling s.out result for different situations

def exit_compl_single_key(f, s, k):
    '''
    ke<tab> to key=" (with doc)
    '''
    l('exit_compl_single_key')
    dfl = dflt(s, k)
    ok, apo = k + '=', ''
    if is_str(dfl):
        apo = '"'
        ok += apo

    dfl = '-' if dfl == T.no_dflt else dfl
    dfl = ok + '[%s]%s' % (dfl, apo)
    s.sh_compl.append(ok)
    s.sh_compl.append(dfl)
    #func_doc(f, s, prefix=dfl, hilite={k: ulen(k)})
    sys_exit(f, s)


def exit_compl_single_val(f, s, key, val):
    l('exit_compl_single_val')
    if not val:
        # key1=<tab> or key1="<tab>
        # we show the doc and the default
        # first a char. prefenting completion when doc and param start with
        # same value ;-)
        s.sh_compl.append(T.spc)
        s.sh_compl.append(key_and_dflt(s, key))
        s.hilite = {key: ulen(key)}
        func_doc(f, s)
        sys_exit(f, s)

    dfl = validate_type_of_val_vs_dflt(f, s, key, val)
    if ' ' in val:
        # this is unfortunatelly uncompletable - if we don't want to replace
        # spaces in values with fake spaces (and we don't, mindset right now.
        # I'mean - we could demand the enter key proxy and fix those with enter
        # key hits but I think the general user is more happy about a
        # requirement less for the price of having no completion here:
        sys_exit(f, s)

    sdfl = str(dfl)
    # we complete if he starts typing the default:
    out = val
    if f.dflt_compl:
        if val and sdfl.lower().startswith(val.lower()) \
                and not sdfl == T.no_dflt:
            if not type(dfl) in (float, int) or f.dflt_compl_nrs:
                out = sdfl
    #if val != '':
    #    s.out += s.apo_miss
    s.sh_compl = [out]
    sys_exit(f, s)


def exit_compl_multi_key(f, s, keys):
    '''he is about to complete a key with multiple matches'''
    l('exit_compl_multi_key')
    pref, h = longest_match(keys), {}

    pl = ulen(pref)
    for k in keys:
        s.sh_compl.append(k) # show
        h[k] = pl            #  hilite
    s.hilite = h
    func_doc(f, s, prefix=pref)
    sys_exit(f, s)


def key_and_dflt(s, k):
    'how a key is shown in the completion list'
    dfl = dflt(s, k)
    dfl = '=' if dfl == T.no_dflt else '[=%s]' % dfl
    return '%s%s' % (k, dfl)


def longest_match(keys):
    if not keys: return 0
    if len(keys) == 1:
        return keys[0]
    k, c = list(keys[0]), ''
    while k:
        c += k.pop(0)
        if not all([True if o.startswith(c) else False for o in keys[1:]]):
            c = c[:-1]
            return c
    return c


# --------------------------------------------------- Formatting of Doc and Sig

# need a tiny bit of unicode api, for textlengths vs. terminal width:
u8 = 'utf-8'
from functools import partial
uni = partial(unicode, encoding=u8)
#uni  = lambda s: unicode(s, encoding=u8) # funtools import justified? no.
ulen = lambda s: len(uni(s))

def mod_doc(f, s):
    m = 'Available Functions:'
    s.res.append(len(m) * '-')
    s.res.append(m + T.spc * (f.term_width - len(m)))
    s.res.append(len(m) * '-')
    for f in f.funcs:
        s.res.append(f)
    s.res.append(T.spc)

def func_doc(f, s, prefix='', into=None):
    '''prefix because this could be shown while a completion must be done
    as well'''
    hilite = s.hilite
    s.prefix = prefix # TEST !!
    if hilite is None:
        hilite = {}
    w = f.term_width
    len_pr = len(prefix)
    if into is None:
        into = s.sh_compl

    d = (s.reg['doc'] or '(no doc)').splitlines()
    if not f.doc_show:
        d = []
    if prefix:
        d.insert(0, prefix)
    e = fmt_err(f, s) if s.err else ''
    dash = T.hilite_norm if not s.func_st == T.func_st_compl else T.hilite_norm_compl
    border = (w - ulen(e)) * dash + e
    #border = uni(w * '-')
    d.append(border)
    #d.append(e) if e else 0
    hsig, vsig = ([], []), ([], [])
    sigm = {'kvs': None, 'hsig': hsig, 'vsig': vsig, 'hilite': hilite}

    def build_sig(f=f, s=s, sigm=sigm, w=w):
        '''py2 just have getargspec. rebuild the signature from it'''
        lsi = sigm['hsig'][0] # the horizontal sig line
        lhi = sigm['hsig'][1] # our markup line below the sig
        vsi = sigm['vsig'][0] # vertical sig, each entry a hori-line
        vhi = sigm['vsig'][1] # vertical hilite, each entry a col0 marker
        def add(s):
            lsi.append(s)
            lhi.append(ulen(s) * dash)
        def addv(line, hvc):
            vsi.append(line)
            vhi.append(hvc)

        dss = s.func_st[0] # status
        # function name:
        fn = s.func.rsplit('.', 1)[-1] # only last part show
        add(dss + fn + '(')
        addv(fn + s.func_st[1], '') # funcname and func status
        # args:
        ak, args = s.reg['arg_keys'], s.reg['args']
        hilite = sigm['hilite']
        for k in ak:
            v = (s.kvs_seen if f.sig_rpl_dflts else args).get(k, args.get(k))
            v = '' if v == T.no_dflt else '=%s' % v
            kv = '%s%s' % (k, v)
            pre = '' if k == ak[0] else ', '
            pkv = pre + kv
            ulen_kv = ulen(kv)
            if not k in hilite:
                lsi.append(pkv)
                hi_char = 'hilite_norm' if k in s.args_left else 'hilite_have'
                if k == s.err_key:
                    hi_char = 'hilite_err_key'
                lhi.append(ulen(pre) * dash)
                lhi.append(ulen_kv * getattr(T, hi_char))
                addv(kv, getattr(T, hi_char + 'v'))
                continue
            lsi.append(pkv)
            if pre:
                lhi.append(2 * dash)
            have = hilite[k]
            lhi.append(have * T.hilite_have_key)
            lhi.append((ulen_kv - have) * T.hilite_req)
            addv(kv, T.hilite_reqv)
        add(')' + s.func_st[1])

    if f.sig_show:
        build_sig()
        sigline = ''.join(hsig[0])
        hi_line = ''.join(hsig[1])

        if ulen(sigline) < w and not f.force_vertical:
            d.append(sigline)
            d.append(hi_line + (w - ulen(hi_line)) * dash)
        else:
            vsi, vhi = vsig
            for i in range(len(vhi)):
                h = '  ' + vhi[i] + ' ' if vhi[i] else ''
                d.append(h + vsi[i])
            # vertical sig display:
            d.append(w * dash)

    # we have the output lines in an array. we build one huge string without(!)
    # and linesep but filled to right which just the right amount of non break
    # spaces:
    out = ''
    for line in d:
        line = uni(line)
        while len(line) > 0:
            chunk = line[:w]
            chunk += uni(T.spc) * (w - len(chunk))
            line = line[w:]
            out += chunk.encode(u8)

    # back from lalaland to what the machine needs:

    into.append(out)
    s.doc_built = True

# -------------------------------------------------- Sys.exit with print result

def sh_doc(f, s):
    if s.reg:
        func_doc(f, s, into=s.res)
    else:
        mod_doc(f, s)
        if s.err:
            s.res.append(fmt_err(f, s))

def fmt_err(f, s):
    return '%s%s%s' % (T.warn_pre, s.err, T.warn_post)

def sys_exit(f, s):
    '''code says: s.err = ...; sys_exit or s.sh_compl=...; sys_exit'''
    if s.err:
        # we do not show any completion.
        s.func_st = T.func_st_err
        sh_doc(f, s)
        done(f, s)
    if s.sh_compl:
        s.compl_prefix = sorted(s.sh_compl)[0]
        [s.res.append(c) for c in s.sh_compl]
        done(f, s)

    s.res = ''
    done(f, s)

def done(f, s):

    if len(s.res) == 1 and s.doc_built:
        # e.g. at exception:
        # only one line of docu would kill the completion
        s.res.insert(0, '-')

    for line, i in zip(s.res, range(len(s.res))):
        l(i, line)
    out = '\n'.join(s.res)
    if not s.help_shown:
        out = out.replace(' ', T.spc)
    out += '\n'
    h = height(f.term_width, out) + 3
    l('height %s.' % h)
    l('\n')
    print('%s.%s' % (f.cmd, s.func))
    print(h)
    print(out)
    sys.stdout.flush()
    if debug or f.testmode:
        if f.testmode:
            raise ComplTestmodeExc(out, 'err')
    sys.exit(0)


def height(w, out):
    r = 0
    for line in out.splitlines():
        r += ((ulen(line) - 1) / w ) + 1
    return r


# ----------------------------------------------------- Help System (...?<TAB>)
# we show the docu of functions, whatever the indexer gave us
def show_help(f, s):
    s.help_out = []  # storing result
    # how many '?':
    m = f.load_file('doc.py')
    s.help_docu = d = m['docu']
    s.func = s.line.split(' ', 1)[0]
    match_entered_func(f, s, all_=d.keys())
    match = sorted(s.func_matches)[0] if s.func_matches else ''
    for i in range(1, 10):
        if f.line[-(i+1)] != '?':
            break
    show_help_for(f, s, match, level=i)
    h = s.help_out
    if h:
        h.append('***')
        md = '\n'.join(h)
        d_mdvl = f.d_cfg + '/modules/mdvl'
        sys.path.insert(0, d_mdvl)
        try:
            import mdvl
            md = mdvl.main(md, term_width=f.term_width, no_print=True)[0]
        except:
            sys.stderr.write('Have no mdvl hilite - plain output:\n')
        sys.stderr.write('\n' + md + '\n')
    return match

def parse_func_code(lines):
    sig, doc, body = _parse_func_code(lines)
    try:
        sig = '\n'.join(sig)
        sig = sig.rsplit(':', 1)[0].split('def ', 1)[1]
    except Exception as ex:
        import pdb;pdb.set_trace()
    body = body.strip()
    i = len(sig) - len(sig.lstrip())
    if i:
        body = body.replace('\n' + ' ' * i, '\n')
    return sig, doc, body

def _parse_func_code(lines):
    from inspect import cleandoc
    if len(lines) == 1:
        _ = lines[0].split(':', 1)
        return [_[0] + ':'], '', _[1]

    sig, doc = [], []
    while lines:
        l = lines.pop(0)
        sig.append(l)
        if l.rstrip().endswith(':'):
            break

    l = '\n'.join(lines).strip()
    for apo in "'''", '"""', "'", '"', '':
        if l.startswith(apo):
            break
    if not apo:
        # no docstring
        return sig, '', lines
    l = l.split(apo, 2)
    return sig, cleandoc(l[1]), l[2]




def show_help_for(f, s, name, level):
    '''print stuff (with ansi codes) to stderr'''
    md = []
    _ = s.help_docu.get(name)
    docu, type = _['d'].strip(), _['t']
    md.append('%s **%s**:' % (type.capitalize(), name or f.cmd))
    if type == 'function':
        sig, doc, body = parse_func_code(docu.splitlines())
        md.append('> ' + sig)
        md.append('\n' + doc)
        if level > 1:
            md.append('```\n%s\n```' % body)
    else:
        md.append('\n' + docu)
    md.insert(0, '---\n')
    s.help_out.extend(md)

    if level > 1 and not type == 'function':
        for k in sorted(s.help_docu.keys()):
            ksub = k[len(name):]
            if k != name and not '.' in k[1:]:
                show_help_for(f, s, k, level-1)




# -------------------------------------------------------------- Highlevel Flow
def main(f):
    '''
    - find/complete the actual function
    - go through complete key values
    '''
    if 0: # testing replies in real life on the cli:
        print '\n abc\n abd\n'
        #print '\nfoo="» some doc string ⤿ stu\nfoo=\n'
        sys.exit(0)

    f.setup() # read the module index file
    s = State()
    s.res = []
    s.sh_compl = []
    f.line = f.line.replace(T.spc, ' ')

    # the principal cmd is not relevant for parsing
    s.line = f.line[len(f.cmd) + 1:]
    s.match_substr = ( True if f.match_substr == True or
                       ( s.line.startswith(' ') and f.match_substr=='on_demand')
                       else False )

    l('fline', f.line, 'sline', s.line, s.match_substr)
    s.line = ln = s.line.strip()
    if ln.endswith('?'):
        match = show_help(f, s) # will print infos on stderr.
        while s.line.endswith('?'):
            s.line = s.line[:-1]

    # func until first space:
    s.func = s.line.split(' ', 1)[0].split(T.spc, 1)[0]
    match_entered_func(f, s)
    l('funcm', s.func_matches)

    if not s.func_matches:
        s.err = Err.func_unknown % f.line.strip()
        sys_exit(f, s)

    if len(s.func_matches) > 1:
        # we have more matching functions. show them, done:
        s.sh_compl = s.func_matches
        sys_exit(f, s)

    fm0 = s.func_matches[0]
    # if its fun<tab> we reply with 'fun' -> bash will insert a space then:
    if f.line.endswith(s.func):
        s.sh_compl = [fm0]
        sys_exit(f, s)

    # a pathologic case: subs <tab> (we can't change the subs anymore)
    if f.match_substr and f.line.endswith(s.func + ' ') and fm0 != s.func:
        s.err = Err.func_unknown % s.func
        sys_exit(f, s)

    s.func = fm0
    s.reg = f.reg[s.func]
    scan_blocks(f, s)



if __name__ == '__main__':
    main(Facts())




