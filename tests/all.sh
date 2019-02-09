#!/bin/bash

echo "getting $foo1 $foo2 :-)"
python -c "import os; print('bla%s' % s.environ['foo3'][:-4])"

set -e
./tests/test_indexer.py
./tests/test_completer.py
