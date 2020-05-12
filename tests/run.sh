if [ "$1" = "" ] || [ ! -f "$1" ]; then
    echo "Usage run.sh <test_file.py> [input_file] [--mac]"
    exit 1
fi
if [ -f "$2" ]; then
    inputs="$2"
fi
flag=""
if [ "$2" = "--mac" ]; then 
    flag="$2"
elif [ "$3" = "--mac" ]; then
    flag="$3"
fi
# compiler and run test file
python2.7 ../compile.py "$1" "$flag" > tmp.s
gcc tmp.s -g -lgc ../runtime.c -o tmp
$(cat $inputs | ./tmp > test_output)
$(cat $inputs | python2.7 "$1" > python_output)
# rm tmp tmp.s
if [ "$(cat test_output)" != "$(cat python_output)" ]; then
    echo "test failed; diff:"
    echo "compile.py out\t\t\t\t\t\t\tPython2.7 out"
    diff -y test_output python_output
    exit 1
fi
rm tmp tmp.s test_output python_output

echo "test passed"