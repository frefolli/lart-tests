#!/bin/bash
set -ex

LARTC="../lartc/builddir/lartc -Iinclude"
CC=clang

$LARTC tests/diff/array-access/source.lart         -o tests/diff/array-access/program.exe
$LARTC tests/diff/array/source.lart                -o tests/diff/array/program.exe
$LARTC tests/diff/chatgpt/source.lart              -o tests/diff/chatgpt/program.exe
$LARTC tests/diff/comments/source.lart             -o tests/diff/comments/program.exe
$LARTC tests/diff/function-pointer/source.lart     -o tests/diff/function-pointer/program.exe
$LARTC tests/diff/hello/source.lart                -o tests/diff/hello/program.exe
$LARTC tests/diff/include-files/source.lart        -o tests/diff/include-files/program.exe
$LARTC tests/diff/merging-declarations/source.lart -o tests/diff/merging-declarations/program.exe
$LARTC tests/diff/raylib/source.lart               -o tests/diff/raylib/program.exe -lraylib
$LARTC tests/diff/regex/source.lart                -o tests/diff/regex/program.exe
$CC    tests/diff/streams-and-floats/source.c -c   -o tests/diff/streams-and-floats/source.o
$LARTC tests/diff/streams-and-floats/source.lart   -o tests/diff/streams-and-floats/program.exe tests/diff/streams-and-floats/source.o
$LARTC tests/diff/strucs-as-rvalue/source.lart     -o tests/diff/strucs-as-rvalue/program.exe
$LARTC tests/diff/strucs/source.lart               -o tests/diff/strucs/program.exe
$LARTC tests/diff/tree/source.lart                 -o tests/diff/tree/program.exe
$LARTC tests/diff/ts/source.lart                   -o tests/diff/ts/program.exe -ltree-sitter -ltree-sitter-lart
$LARTC tests/diff/variadic/source.lart             -o tests/diff/variadic/program.exe
