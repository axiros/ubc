# Testing the Completer

## Verifying real completion on the cli

source `cli_verify.sh`

Then `mm fu<tab>`...


## Debugging: Step through code

If you have an error in real life, create the input line up to the tab hit in a
test function - you can trace through code then.


You can even step through breakpoints or real completer calls, i.e. from the
cli - if you remove the backticks from the python call in the test script.
No stdin though, set it to fd 0 if you can't type w/o seeing what you type.

## Adding more tested use cases

- Change "mm" module in `setup.py` in the tests dir.
- Don't change existing functions, would break the tests
- But you can add new functions, tests should be robust against that.
- Then run `test_indexer.py`


## Proper Test Foreground Prints

    export b2pt_term_width="$COLUMNS"

in the terminal you run the tests. After resizing again, should be clear ;-)

> Sometimes its useful to inspect fake space lines not fitting into the terminal, though.


## See the fake space

Do this:

    export b2pt_spc=-

Then run the tests again in foreground, you'll see the fake spaces then, e.g.:

    --▷-boolsch=True--------
