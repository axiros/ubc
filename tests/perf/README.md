# Comparing Perf

1. When running python calls like python -Ssc `"$var_from_here_doc"`
2. Or python -Ss <filename>


repeatadly.

Result:

```
1 ~/GitHub/b2p/tests/perf $ python -m timeit "import os; os.system('./inline.sh')"
10 loops, best of 3: 534 msec per loop
1 ~/GitHub/b2p/tests/perf $ python -m timeit "import os; os.system('./call.sh')"
10 loops, best of 3: 495 msec per loop
1 ~/GitHub/b2p/tests/perf $
```

loading from a file is even a bit faster =>

**no huge performance gain by packing python modules into bash scripts as it seems.**



