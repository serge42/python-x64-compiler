
# Compiler Construction

Author: Sébastien Bouquet; bouqus@usi.ch

Usage: Python2.7 compile.py <prgrm.py> [--mac] [--flatten] [--pseudo] [--liveness]

    <prgrm.py> is a python file using print_function (produces the same output as python2.7 `print <tuple>` when only one argument is passed).

Limitations:

    Arrays not working  
    Hashmaps not working  
    String and float missing  
    While not working  

## Tests

Tests can be run using _run.sh_ <test_file.py> [inputs] [--mac]

    [inputs] is a text file containing one integer value per line. These values are passed to <test_file.py> when it calls the "input" function.

### Tests available

- print.py: simple test of the print function (pass)
- input.py: simple test of the input function (pass)
- binops.py: test of intricate arithmetic operations, and some dead code. (pass)
- spilling.py: test with many variables and operations to force the compiler to spill.
- ifelse.py: test a simple if/else statement
- while.py: test a simple while loop (fail)
