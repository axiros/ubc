#!/bin/bash

echo "getting $foo1 $foo2 :-)"
python -c "import os; print('bla%(foo1)s%(foo2)s' % os.environ)"

set -e
./tests/test_indexer.py
./tests/test_completer.py
