#!/bin/bash

# If the input parameter is all, run all tests.
if [ "$1" == "all" ]; then
    pytest test
elif [ -n "$1" ]; then
    # If the input file exists, test the input file.
    pytest $1
else
    # If nothing is input, test all.
    pytest test
fi