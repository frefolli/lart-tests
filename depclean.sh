#!/bin/bash

set -ex
./clean.sh
rm -rf ./tests/diff/array-access/program.out
rm -rf ./tests/diff/array/program.out
rm -rf ./tests/diff/chatgpt/program.out
rm -rf ./tests/diff/comments/program.out
rm -rf ./tests/diff/function-pointer/program.out
rm -rf ./tests/diff/hello/program.out
rm -rf ./tests/diff/include-files/program.out
rm -rf ./tests/diff/merging-declarations/program.out
rm -rf ./tests/diff/raylib/program.out
rm -rf ./tests/diff/regex/program.out
rm -rf ./tests/diff/streams-and-floats/program.out
rm -rf ./tests/diff/strucs-as-rvalue/program.out
rm -rf ./tests/diff/strucs/program.out
rm -rf ./tests/diff/tree/program.out
rm -rf ./tests/diff/ts/program.out
rm -rf ./tests/diff/variadic/program.out
