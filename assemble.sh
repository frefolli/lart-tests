# Difference
mkdir -p tests/diff/array-access/
mkdir -p tests/diff/array/
mkdir -p tests/diff/chatgpt/
mkdir -p tests/diff/comments/
mkdir -p tests/diff/function-pointer/
mkdir -p tests/diff/hello/
mkdir -p tests/diff/include-files/
mkdir -p tests/diff/merging-declarations/
mkdir -p tests/diff/raylib/
mkdir -p tests/diff/regex/
mkdir -p tests/diff/streams-and-floats/
mkdir -p tests/diff/strucs-as-rvalue/
mkdir -p tests/diff/strucs/
mkdir -p tests/diff/tree/
mkdir -p tests/diff/ts/
mkdir -p tests/diff/variadic/

cp ../lart-examples/array-access.lart         tests/diff/array-access/source.lart
cp ../lart-examples/array.lart                tests/diff/array/source.lart
cp ../lart-examples/chatgpt.lart              tests/diff/chatgpt/source.lart
cp ../lart-examples/comments.lart             tests/diff/comments/source.lart
cp ../lart-examples/function-pointer.lart     tests/diff/function-pointer/source.lart
cp ../lart-examples/hello.lart                tests/diff/hello/source.lart
cp ../lart-examples/include-files.lart        tests/diff/include-files/source.lart
cp ../lart-examples/merging-declarations.lart tests/diff/merging-declarations/source.lart
cp ../lart-examples/raylib.lart               tests/diff/raylib/source.lart
cp ../lart-examples/regex.lart                tests/diff/regex/source.lart
cp ../lart-examples/streams-and-floats.lart   tests/diff/streams-and-floats/source.lart
cp ../lart-examples/strucs-as-rvalue.lart     tests/diff/strucs-as-rvalue/source.lart
cp ../lart-examples/strucs.lart               tests/diff/strucs/source.lart
cp ../lart-examples/tree.lart                 tests/diff/tree/source.lart
cp ../lart-examples/ts.lart                   tests/diff/ts/source.lart
cp ../lart-examples/variadic.lart             tests/diff/variadic/source.lart

# Failing
mkdir -p tests/fail/decl-type-checking/
mkdir -p tests/fail/duplicate-definition/
mkdir -p tests/fail/include-directives/
mkdir -p tests/fail/name-resolution/
mkdir -p tests/fail/syntax/
mkdir -p tests/fail/type-checking/

cp ../lart-examples/bad-decl-type-checking.lart   tests/fail/decl-type-checking/source.lart
cp ../lart-examples/bad-duplicate-definition.lart tests/fail/duplicate-definition/source.lart
cp ../lart-examples/bad-include-directives.lart   tests/fail/include-directives/source.lart
cp ../lart-examples/bad-name-resolution.lart      tests/fail/name-resolution/source.lart
cp ../lart-examples/bad-syntax.lart               tests/fail/syntax/source.lart
cp ../lart-examples/bad-type-checking.lart        tests/fail/type-checking/source.lart
