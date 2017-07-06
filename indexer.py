'''
Handling rt_loadmod
Writes module completion information into a config directory.

depth: module import depth
cdepth: Inner class depth

We write TWO files per command:
    - defs.py: For the short tab complection lookups. Contains sigs and
      reduced docstrings, we have no coloring here.
      Remember that at each tab hit that file must be read again, we restart
      Python all the time again (no coproc).
    - doc.py: For ?<TAB> hits: Displays full infos, reading the doc.py

'''
# we have a lot of time in this one:
import sys, os
from inspect import getargspec, getdoc, getsource, ismodule
from fnmatch import fnmatch

# Facts (from outside)
class Facts:
    # defaults:
    d_cfg     = None  # config dir, we write into this
    modn      = None  # module to index (when called from command line)
    fmatch    = '*'   # what functions to index
    mmatch    = '*'   # what modules to index
    cmatch    = '*'   # what classes to index
    depth     = 1     # import follow depth
    cdepth    = 2     # nested objects within a mod follow depth
    py_path   = None  # add this to sys.path before importing
    mod       = None  # inline callers could give a facts instance with a loaded
                      # mod. No import trying then.
    max_doc_lines = 5 # max lines to show on doc string while completing

class State:
    def __init__(self):
        self.funcs = []
        self.reg = {}
        self.doc = {}
        self.mod = None # module to index
        self.n = None # item name
        self.ccount = 0 # class depth counter within module


# debug:
def l(*m): print ' '.join([str(s) for s in m])

def matches(fn, match):
    #TODO: Regex
    # match is global, set in __main__ by -m
    return fnmatch(fn, match)

#def getsig(func, args, m):
#    import pdb; pdb.set_trace()

def doc_tag_line(f, func):
    '''what to show when func infos are shown while completing'''
    # that will be later shown in completions, w/o linesep possibilities
    # -> do the full infos (for ?<tab>) in s.doc
    # trying to get to a summary

    doc = (getdoc(func) or '').strip()
    doc = doc.split('\n', f.max_doc_lines)[:f.max_doc_lines]
    d = ''
    for i in range(len(doc)):
        if not doc[i]:
            return d.strip()
        d += '\n' + doc[i]
        if d[-1] in '!.':
            return d.strip()
    d = d.strip()
    return d if i < f.max_doc_lines else d + '(...)'


def parse_func(n, func, prefix, f, s, typ='function'):
    '''inspect function signature
    # TODO: py3 inspect changed.
    '''
    prefix += (n,)
    s.doc[prefix] = {'t': typ, 'd': getsource(func)}
    fn = '.'.join(prefix[1:])
    if not matches(fn, f.fmatch):
        return
    s.funcs.append(fn)
    args = getargspec(func)
    m = { 'pos_args': [], 'doc': doc_tag_line(f, func)
        , 'arg_keys': args.args, 'args': {}}
    defs = list(args.defaults or ())
    for a in reversed(args.args):
        d = m['args'][a] = defs.pop() if defs else 'n.d.'
        if d == 'n.d.':
            m['pos_args'].insert(0, a)
    #m['sig'] = getsig(func, args, m)
    s.reg[fn] = m
    l('added', 'function' , prefix)

pub_args = lambda obj: [(n, getattr(obj, n))
           for n in dir(obj) if not n.startswith('_')]

def parse_cont(cont, prefix, f, s):
    '''recurse into, depths'''
    # too deep? cdepth is for objects per module, depths is for module imports
    if ismodule(cont):
        mtch = f.mmatch
        s.ccount = 0 # cdepth start new per module
        if len(prefix) > f.depth - 1:
            return
    else:
        mtch = f.cmatch
        if s.ccount > f.cdepth:
            return
        s.ccount += 1
    try:
        n = cont.__name__
    except Exception as ex:
        import pdb;pdb.set_trace()
    typ = type(cont).__name__
    if not matches(n, mtch):
        return
    prefix += (n,)
    l('added', typ, prefix)
    s.doc[prefix] = { 't': typ, 'd': getdoc(cont) or ''}
    items = pub_args(cont)
    [ parse_func(n, v, prefix, f, s) if hasattr(v, '__code__') else
      parse_cont(v, prefix, f, s) if hasattr(v, '__name__')  else None
      for n, v in items ]

def main(f):
    ''' entry point for inline calls. give it a facts instance'''
    s = State()
    if f.mod:
        s.mod = f.mod
    else:
        try:
            s.mod, s.n = __import__(f.modn), f.modn.rsplit('.', 1)[-1]
        except Exception as ex:
            raise Exception('Could not import: %s.' % str(ex))

    for m in 'cmatch', 'mmatch', 'fmatch':
        mv = getattr(f, m)
        if not '*' in mv:
            setattr(f, m, '*' + mv + '*')

    parse_cont(s.mod, (), f, s)

    d_m = "%s/var/funcs/%s" % (f.d_cfg, s.n)
    s.funcs = sorted(s.funcs)
    l('writing', s.funcs)
    os.system('mkdir -p "%s"' % d_m)
    with open(d_m + '/defs.py', 'w') as fd:
        fd.write('funcs = %s' % str(s.funcs))
        fd.write('\nreg = %s' % s.reg)

    doc = s.doc
    # to dotted format:
    for k in list(doc.keys()):
        doc['.'.join(k[1:])] = doc.pop(k)
    from pprint import pformat
    with open(d_m + '/doc.py', 'w') as fd:
        fd.write(pformat(doc))



if __name__ == '__main__':
    f = Facts()
    args = list(sys.argv[1:])
    try:
        while args:
            a, v = args.pop(0).split('=')
            _ = getattr(f, a) # to crash on wrong arg
            v = int(v) if v.isdigit() else v
            l('setting', a, 'to', v)
            setattr(f, a, v)
    except:
        k = dict(pub_args(f))
        raise Exception('Supply <arg1>=<val1> <arg2>=<v2>... from', k)
    main(f)

