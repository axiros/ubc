#!/bin/bash

echo "getting $foo1 $foo2 :-)"


set -e
./tests/test_indexer.py
./tests/test_completer.py
