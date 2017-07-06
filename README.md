# b2p.compl: Bash2Python Completer

```
1 ~/GitHub/b2p $ python -Ss './completer.py' /tmp/test_b2p_compl mm 'mm fun1 j="23" b' '' $COLUMNS
boolsch=
boolsch=[True]                                                                                                                               fun1 doc                                                                                                                                     line2                                                                                                                                        --------------------------------------------------------------------------------------------------------------------------------------------- »fun1(j, i=23, foo=bar, boolsch=True, fl=1.23)«                                                                                             -------------------------▲▲▲▲▲▲▲△△△△△--------------------------------------------------------------------------------------------------------
1 ~/GitHub/b2p $
```

# Tech

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

### Too Much Space(s)

This is very much harder. The completer works against us here and we have to
fool it.

Here the problem:

Example:

    def fun(foo=True, bar=0): pass

and when the user enters `mod foo=T<tab>` we want to complete, so that he has
`mod foo=True bar=` in the current line.

Doing (naively) this:

    mm fun foo=T<tab>   --> \nTrue bar="\n


would make the completer think there are two different options a `True` and a
`bar` one - and so he acts:

    2 ~/GitHub/b2p $ mm fun foo=T<tab> (completer exits with \nTrue bar=\n
    True  bar="
    2 ~/GitHub/b2p $ mm fun foo=T

Ups.

> You could play around with `$IFS` but you'll never fix the behavior really
> satisfactory, according to our findings.

The hack to get around the spaces problem is this:



### The (No)Space Hack

Instead of an ASCII space we return something spacey.

The [non breaking space](https://en.wikipedia.org/wiki/Non-breaking_space) looks exactly like a real one - assumed on a non stone age terminal.

For the completer this is a normal (non seperating) character - for the human eye it is a space:

    2 ~/GitHub/b2p $ mm fun foo=T<tab>
    2 ~/GitHub/b2p $ mm fun foo=True\xc2\xa0bar= # completer exitted with \nTrue\xc2\xa0bar=\n


This is the main hack.
Then there is a minor problem left to solve:

### The Double Options Return Hack

Say the function is like

    def fun(foo=True, bar='str'): pass

and we want to complete

    mod fun foo=T<tab>

with

`mod fun foo=True\xc2\xa0bar="`

but ending with a double quote (because of the string default in the signature)
would cause the completer to add a space behind the apo:

    2 ~/GitHub/b2p $ mm fun foo=True bar=" <---cursor here

This one we solve by not ONLY exitting with `...bar="` but also, as a second
alternative to the completer with `...bar="\xc2\xa0`. Then he HAS stop the
cursor behind the apostrophe - and the user can happily enter the string value
required.


### Further Complications

Should you zap over the code pls have in mind that the actual
line to be completed can be a wild mix of real and `fake` spaces. User will
always type real spaces before hitting <tab>, completer adds fake ones.

The complication is in the exit values required dependent on that:

Example:  If we want to complete `foo b` into options `foo bar` and `foo baz` then we need to exit with:

    foo b<tab>        --> \nbar\nbaz\n
    foo\xc2\xa0b<tab> --> \nfoo\xc2\xa0bar\nfoo\xc2\xa0baz\n

and there are in general many combinations.



### Displaying Information to the User While Completing


To display e.g. function doc strings or default values to the user after a tab
hit we have two options.


#### Keeping the Line

The completer keeps the line like it is when we just exit with lines which
don't start with the same character. Then there can't be no completion and the
user will see the information presented as options.


#### Not Keeping the Line

When there is much information to show we just print it on stderr. That does
break the line since this just starts where the cursor is.

> No, moving the cursor up a few lines via escape codes and then back to where it was, using `$COMP_POINT` is not an option since we do not know the length of the rendered prompt.

The user than looses the current line but gets it back by hitting <tab> again.










