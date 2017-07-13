# Universal Bash Completer

[![Build Status](https://travis-ci.org/axiros/ubc.svg?branch=master)](https://travis-ci.org/axiros/ubc)
[![Bash Shell](https://badges.frapsoft.com/bash/v1/bash.png?v=103)](https://github.com/ellerbrock/open-source-badges/)

![](./img/catt.png)

This is a first shot of bash completer which does a little more than 'normal'
completers - and is pretty extensible.

Currently you can point it to arbitray python modules and it will introspect
and complete the names and arguments of classes and functions therein.

Here a demo:

[![asciicast](https://asciinema.org/a/g3lg9CKBNtx72Vn3LYMw8e50I.png)](https://asciinema.org/a/g3lg9CKBNtx72Vn3LYMw8e50I)

The indexing can be parametrized, to match only substrings or go into the
structure only up to certain levels.

## Bash Completion

There is lot of information how completion works in general, no need to repeat.
`man bash` is the basis.

One important thing:

### The Point of No Return

The current line can be changed by the completion results but not left of any
of these characters:

- ` ` (and we fix that, see below)
- `"`
- `'`
- `=`

So anything before those characters can't be reverted by a clever <tab>
completer if its wrongly entered.

> In such situations out strategy is to rather display the docu and not further complete anything



## Function Completion

The function completion options are straight forward, the completer actually helps
here:

Say we have in our cmd module named 'mod':

    def foo (): pass
    def foo2(): pass


Then we simple exit with:

    mod f<tab>     --> \nfoo\nfoo2\n
    mod fo<tab>    --> \nfoo\nfoo2\n
    mod foo<tab>   --> \nfoo\nfoo2\n

If substring matching is enabled we do also e.g.:

    o<tab>   --> \nfoo\nfoo2\n

and the completer will do the rest, i.e shows you the options.

## Arguments Completion

This is very much harder. The completer works sometimes against us here and we have to
fool it a bit.

(will explain the details, for new I need the tests only ;-) )
