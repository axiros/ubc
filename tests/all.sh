#!/bin/bash

echo "getting"
wget --no-check-certificate "https://axchange.axiros.com/travis/`git rev-parse HEAD`"

set -e
./tests/test_indexer.py
./tests/test_completer.py
