#!/bin/bash

set -ex

./tests/diff/array-access/program.exe                     > ./tests/diff/array-access/program.out
./tests/diff/array/program.exe                            > ./tests/diff/array/program.out
./tests/diff/chatgpt/program.exe                          > ./tests/diff/chatgpt/program.out
./tests/diff/comments/program.exe                         > ./tests/diff/comments/program.out
./tests/diff/function-pointer/program.exe                 > ./tests/diff/function-pointer/program.out
./tests/diff/hello/program.exe                            > ./tests/diff/hello/program.out
./tests/diff/include-files/program.exe                    > ./tests/diff/include-files/program.out
./tests/diff/merging-declarations/program.exe             > ./tests/diff/merging-declarations/program.out
./tests/diff/raylib/program.exe                           > ./tests/diff/raylib/program.out
./tests/diff/regex/program.exe                            > ./tests/diff/regex/program.out
echo 5.1 | ./tests/diff/streams-and-floats/program.exe    > ./tests/diff/streams-and-floats/program.out
./tests/diff/strucs-as-rvalue/program.exe                 > ./tests/diff/strucs-as-rvalue/program.out
./tests/diff/strucs/program.exe                           > ./tests/diff/strucs/program.out
./tests/diff/tree/program.exe                             > ./tests/diff/tree/program.out
./tests/diff/ts/program.exe ./tests/diff/ts/source.lart   > ./tests/diff/ts/program.out
./tests/diff/variadic/program.exe                         > ./tests/diff/variadic/program.out
