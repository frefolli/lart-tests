from __future__ import annotations

import enum
import os
import yaml
import argparse
import sys

class TextColor(enum.Enum):
  RED="\x1b[1;31m"#]
  GREEN="\x1b[1;32m"#]
  PURPLE="\x1b[1;35m"#]
  AZURE="\x1b[1;36m"#]
  NORMAL="\x1b[0;39m"#]

  def begin(self):
    print(self.value, end='')

  def end(self):
    print(TextColor.NORMAL.value, end='')

def read_yaml(path: str) -> dict:
  with open(path, 'r') as file:
    return yaml.load(file.read(), Loader=yaml.Loader)

def write_yaml(path: str, obj: dict) -> None:
  with open(path, 'w') as file:
    return yaml.dump(obj, file, Dumper=yaml.Dumper)

class CMD:
  def __init__(self, cmd: str) -> None:
    self.cmd: str = cmd
    self.args: list[str] = []

  def append(self, argx: str|list[str]):
    assert isinstance(argx, str) or isinstance(argx, list)
    if isinstance(argx, str):
      self.args.append(argx)
    elif isinstance(argx, list):
      for arg in argx:
        assert isinstance(arg, str)
        self.args.append(arg)

  def assemble(self) -> str:
    return ' '.join([self.cmd] + self.args)

  def exec(self, verbose: bool) -> int:
    cmdline = self.assemble()
    if verbose:
      print('|>', cmdline)
    return os.system(cmdline)

class Compiler:
  def __init__(self, path: str, include_directories: list[str], options: list[str]) -> None:
    self.path: str = path
    self.include_directories: list[str] = include_directories
    self.options: list[str] = options

  def to_dict(self) -> dict:
    return {
      'path': self.path,
      'include_directories': self.include_directories,
      'options': self.options,
    }

  @staticmethod
  def from_dict(data: dict) -> Compiler:
    return Compiler(
      path = data['path'],
      include_directories = data['include_directories'],
      options = data['options'],
    )

  def compile(self, sources: list[str], links: list[str], output: str, verbose: bool, complaint: str) -> bool:
    cmd = CMD(self.path)
    cmd.append(['-I' + include_directory for include_directory in self.include_directories])
    cmd.append(['-l' + link for link in links])
    cmd.append(sources)
    cmd.append(self.options)
    cmd.append(['-o', output])
    if output.endswith('.o'):
      cmd.append('-c')
    cmd.append(['&>', complaint])

    return cmd.exec(verbose) == 0

class TestKind(enum.Enum):
  SUCC='succ'
  DIFF='diff'
  FAIL='fail'

  @staticmethod
  def values() -> list[str]:
    return [_.value for _ in list(TestKind)]

  @staticmethod
  def enums() -> list[TestKind]:
    return list(TestKind)
  
  @staticmethod
  def parse(value: str) -> TestKind:
    for e in TestKind.enums():
      if e.value == value:
        return e
    raise ValueError('Value `%s` is not valid ofr TestKind' % (value,))

class Test:
  def __init__(self, kind: TestKind, name: str, path: str, sources: list[str], links: list[str], program: str, args: list[str], inputs: list[str], reference: str, output: str) -> None:
    self.kind: TestKind = kind
    self.name: str = name
    self.path: str = path
    self.sources: list[str] = sources
    self.links: list[str] = links
    self.program: str = program
    self.args: list[str] = args
    self.inputs: list[str] = inputs
    self.reference: str = reference
    self.output: str = output

  @staticmethod
  def discover(path: str) -> Test:
    if not os.path.exists(path):
      raise ValueError('Cannot discover test in `%s` because the directory doesn\'t exist' % (path,))
    path_pieces = path.split('/')
    
    if len(path_pieces) < 2:
      raise ValueError('Cannot discover test if the path `%s` isn\'t in the correct format: `[<dir/]<kind>/<name>`' % (path,))
    
    kind = path_pieces[-2]
    name = path_pieces[-1]

    if kind not in TestKind.values():
      raise ValueError('The test kind `%s` isn\'t among the recognized ones: %s' % (kind, TestKind.values()))

    reference = 'program.ref'
    sources = []
    links = []
    inputs = []
    args = []
    for file in os.listdir(path):
      ext = file.split('.')[-1]
      if ext in ['c', 'o', 'lart', 's', 'll']:
        sources.append(file)
      elif ext in ['in']:
        inputs.append(file)
      elif ext in ['ref']:
        reference = file
      elif ext in ['cli']:
        args.append(file)

    program = 'program.exe'
    output = 'program.out'
    return Test(TestKind.parse(kind), name, path, sources, links, program, args, inputs, reference, output)


  def build(self, framework: Framework) -> bool:
    sources = [os.path.join(self.path, source) for source in self.sources]
    c_sources = list(filter(lambda f: f.endswith('.c'), sources))
    lart_sources = list(filter(lambda f: f.endswith('.lart'), sources))
    ll_sources = list(filter(lambda f: f.endswith('.ll'), sources))
    s_sources = list(filter(lambda f: f.endswith('.s'), sources))
    o_sources = set(filter(lambda f: f.endswith('.o'), sources))

    complains = []
    for c_source in c_sources:
      o_source = c_source.replace('.c', '.o')
      if o_source in o_sources:
        raise ValueError('Conflicting CC::out vs LARTC::in => `%s`' % (o_source,))
      o_sources.add(o_source)
      complains.append(o_source.replace('.o', '.com'))
      if (not os.path.exists(o_source)) or (os.path.getmtime(o_source) <= os.path.getmtime(c_source)):
        ok = framework.cc.compile([c_source], [], o_source, verbose=framework.verbose, complaint=complains[-1])
        if not ok:
          return False

    for lart_source in lart_sources:
      o_source = lart_source.replace('.lart', '.o')
      if o_source in o_sources:
        raise ValueError('Conflicting LARTC::out vs LARTC::in => `%s`' % (o_source,))
      o_sources.add(o_source)
      complains.append(o_source.replace('.o', '.com'))
      if (not os.path.exists(o_source)) or (os.path.getmtime(o_source) <= os.path.getmtime(lart_source)):
        ok = framework.lartc.compile([lart_source], [], o_source, verbose=framework.verbose, complaint=complains[-1])
        if not ok:
          return False

    for ll_source in ll_sources:
      o_source = ll_source.replace('.ll', '.o')
      if o_source in o_sources:
        raise ValueError('Conflicting LLVMIR::out vs LARTC::in => `%s`' % (o_source,))
      o_sources.add(o_source)
      complains.append(o_source.replace('.o', '.com'))
      if (not os.path.exists(o_source)) or (os.path.getmtime(o_source) <= os.path.getmtime(ll_source)):
        ok = framework.lartc.compile([ll_source], [], o_source, verbose=framework.verbose, complaint=complains[-1])
        if not ok:
          return False

    for s_source in s_sources:
      o_source = s_source.replace('.s', '.o')
      if o_source in o_sources:
        raise ValueError('Conflicting AS::out vs LARTC::in => `%s`' % (o_source,))
      o_sources.add(o_source)
      complains.append(o_source.replace('.o', '.com'))
      if (not os.path.exists(o_source)) or (os.path.getmtime(o_source) <= os.path.getmtime(s_source)):
        ok = framework.lartc.compile([s_source], [], o_source, verbose=framework.verbose, complaint=complains[-1])
        if not ok:
          return False

    o_sources = list(o_sources)
    program = os.path.join(self.path, self.program)
    complains.append(program.replace('.exe', '.com'))
    ok = True
    if (not os.path.exists(program)) or (os.path.getmtime(program) <= max([os.path.getmtime(o_source) for o_source in o_sources])):
      ok = framework.lartc.compile(o_sources, self.links, program, verbose=framework.verbose, complaint=complains[-1])
    return ok

  def run(self, framework: Framework) -> bool:
    assert self.kind in [TestKind.SUCC, TestKind.DIFF]
    program = os.path.join(self.path, self.program)
    cmd = CMD(program)
    cmd.append(self.args)
    for input in self.inputs:
      cmd.append(['<', os.path.join(self.path, input)])
    cmd.append(['>', os.path.join(self.path, self.output)])
    return cmd.exec(framework.verbose) == 0

  def consolidate(self, framework: Framework) -> None:
    assert self.kind in [TestKind.DIFF]
    output_path = os.path.join(self.path, self.output)
    reference_path = os.path.join(self.path, self.reference)

    if not os.path.exists(output_path):
      raise ValueError('Cannot consolidate test `%s/%s` because it was never executed in the first place')

    cmd = CMD('cp')
    cmd.append(output_path)
    cmd.append(reference_path)
    assert cmd.exec(framework.verbose) == 0

  def compare(self, framework: Framework) -> bool:
    assert self.kind in [TestKind.DIFF]
    output_path = os.path.join(self.path, self.output)
    reference_path = os.path.join(self.path, self.reference)

    if not os.path.exists(output_path):
      raise ValueError('Cannot compare test `%s/%s` because it was never executed in the first place')

    if not os.path.exists(reference_path):
      raise ValueError('Cannot compare test `%s/%s` because it was never consolidated in the first place')

    cmd = CMD('diff')
    cmd.append(output_path)
    cmd.append(reference_path)
    return cmd.exec(framework.verbose) == 0

  def clean(self, framework: Framework) -> None:
    sources = [os.path.join(self.path, source) for source in self.sources]
    c_sources = list(filter(lambda f: f.endswith('.c'), sources))
    lart_sources = list(filter(lambda f: f.endswith('.lart'), sources))
    ll_sources = list(filter(lambda f: f.endswith('.ll'), sources))
    s_sources = list(filter(lambda f: f.endswith('.s'), sources))
    
    o_sources = []
    o_sources += [c_source.replace('.c', '.o') for c_source in c_sources]
    o_sources += [lart_source.replace('.lart', '.o') for lart_source in lart_sources]
    o_sources += [ll_source.replace('.ll', '.o') for ll_source in ll_sources]
    o_sources += [s_source.replace('.s', '.o') for s_source in s_sources]
    
    complains = []
    complains += [c_source.replace('.c', '.com') for c_source in c_sources]
    complains += [lart_source.replace('.lart', '.com') for lart_source in lart_sources]
    complains += [ll_source.replace('.ll', '.com') for ll_source in ll_sources]
    complains += [s_source.replace('.s', '.com') for s_source in s_sources]
    program = os.path.join(self.path, self.program)
    complains.append(program.replace('.exe', '.com'))
    output = os.path.join(self.path, self.output)

    cmd = CMD('rm')
    cmd.append('-rf')
    cmd.append(o_sources)
    cmd.append(program)
    cmd.append(output)
    cmd.append(complains)
    assert cmd.exec(framework.verbose) == 0

  def begin(self, phase: str):
    print('| %s | %s | %s | ..... |' % (
      self.kind.name.ljust(6),
      self.name.ljust(40),
      phase.ljust(12)
    ), end='\r')

  def end(self, phase: str, esit: bool):
    print('| %s | %s | %s | ' % (
      self.kind.name.ljust(6),
      self.name.ljust(40),
      phase.ljust(12)
    ), end='')
    if esit:
      TextColor.GREEN.begin()
      print('PASS'.ljust(5), end='')
      TextColor.GREEN.end()
    else:
      TextColor.RED.begin()
      print('ERROR'.ljust(5), end='')
      TextColor.RED.end()
    print(' |')

  def report(self, framework: Framework) -> None:
    print('#' * 20 + self.name.ljust(20) + '#' * 20)
    with open(os.path.join(self.path, self.output)) as file:
      print(file.read())
    print('#' * 20 + self.name.ljust(20) + '#' * 20)

  def to_dict(self) -> dict:
    return {
      'kind': self.kind.value,
      'name': self.name,
      'path': self.path,
      'sources': self.sources,
      'links': self.links,
      'program': self.program,
      'args': self.args,
      'inputs': self.inputs,
      'reference': self.reference,
      'output': self.output,
    }

  @staticmethod
  def from_dict(data: dict) -> Test:
    return Test(
      kind = TestKind.parse(data['kind']),
      name = data['name'],
      path = data['path'],
      sources = (data.get('sources') or []),
      links = (data.get('links') or []),
      program = (data.get('program') or 'program.exe'),
      args = (data.get('args') or []),
      inputs = (data.get('inputs') or []),
      reference = (data.get('reference') or 'program.ref'),
      output = (data.get('output') or 'program.out'),
    )

class Framework:
  def __init__(self, cc: Compiler, lartc: Compiler, test_dir: str) -> None:
    self.cc = cc
    self.lartc =lartc 
    self.test_dir: str = test_dir
    self.tests: dict[TestKind, dict[str, Test]] = {}
    self.verbose: bool = False

  def to_dict(self) -> dict:
    return {
      'cc': self.cc.to_dict(),
      'lartc': self.lartc.to_dict(),
      'test_dir': self.test_dir,
    }

  @staticmethod
  def from_dict(data: dict) -> Framework:
    return Framework(
      cc = Compiler.from_dict(data['cc']),
      lartc = Compiler.from_dict(data['lartc']),
      test_dir = data['test_dir']
    )

  @staticmethod
  def load_from_config(config_file: str) -> Framework:
    if os.path.exists(config_file):
      return Framework.from_dict(read_yaml(config_file))
    else:
      framework = Framework(
        cc = Compiler('./cc', [], ['-c']),
        lartc = Compiler('./lartc', ['include'], []),
        test_dir = 'tests'
      )
      write_yaml(config_file, framework.to_dict())
      return framework

  @staticmethod
  def discover_tests(path: str) -> dict[TestKind, dict[str, Test]]:
    tests: dict[TestKind, dict[str, Test]] = {}
    for kinddir in os.listdir(path):
      kindpath = os.path.join(path, kinddir)
      if os.path.isdir(kindpath):
        for namedir in os.listdir(kindpath):
          namepath = os.path.join(kindpath, namedir)
          if os.path.isdir(namepath):
            test = Test.discover(namepath)
            if test.kind not in tests:
              tests[test.kind] = {}
            tests[test.kind][test.name] = test
    return tests

  @staticmethod
  def write_tests(tests: dict[TestKind, dict[str, Test]], test_config: str):
    write_yaml(test_config, {key.value:[test.to_dict() for test in value.values()] for (key, value) in tests.items()})

  @staticmethod
  def read_tests(test_config: str) -> dict[TestKind, dict[str, Test]]:
      result: dict[TestKind, dict[str, Test]] = {}
      for kind, tests in read_yaml(test_config).items():
        result[TestKind.parse(kind)] = {}
        for test in tests:
          test = Test.from_dict(test)
          result[test.kind][test.name] = test
      return result

  @staticmethod
  def load_tests(test_dir: str) -> dict[TestKind, dict[str, Test]]:
    if not os.path.exists(test_dir):
      raise ValueError('Cannot load Framework as the test directory `%s` doesn\'t exist' % test_dir)
    if not os.path.isdir(test_dir):
      raise ValueError('Cannot load Framework as the test directory `%s` isn\'t a directory' % test_dir)

    test_config = os.path.join(test_dir, 'config.yml')
    if not os.path.exists(test_config):
      tests = Framework.discover_tests(test_dir)
      Framework.write_tests(tests, test_config)
      return tests
    else:
      return Framework.read_tests(test_config)

  def restore(self):
    self.tests = Framework.load_tests(self.test_dir)

  def save(self):
    test_config = os.path.join(self.test_dir, 'config.yml')
    Framework.write_tests(self.tests, test_config)

  def get_targets(self, raw_targets: list[str]) -> list[Test]:
    targets: list[Test] = []
    kinds: dict[TestKind, set[str]] = {}
    for raw_target in raw_targets:
      pieces = raw_target.split('/')
      if len(pieces) != 2:
        raise ValueError('Invalid target supplied: `%s` is not in format <kind>/<name>' % (raw_target,))
      kind, name = pieces
      if kind not in TestKind.values():
        raise ValueError('Invalid test kind in target supplied: `%s` is not a valid TestKind' % (kind,))
      kind = TestKind.parse(kind)
      if kind not in kinds:
        kinds[kind] = set({})
      kinds[kind].add(name)

    for kind in kinds.keys():
      names = kinds[kind]
      tests_of_that_kind: list[Test] = list((self.tests.get(kind) or {}).values())
      filtered_tests = list(filter(lambda t: t.name in names, tests_of_that_kind))
      filtered_names = set([t.name for t in filtered_tests])
      missing_names = names.difference(filtered_names)
      if len(missing_names) > 0:
        raise ValueError('Invalid test names supplied: %s are not valid test names within kind `%s`' % (names, kind))
      targets += filtered_tests
    return targets

  def clean(self, raw_targets: list[str]):
    targets: list[Test] = []
    if len(raw_targets) == 0:
      targets += list((self.tests.get(TestKind.FAIL) or {}).values())
      targets += list((self.tests.get(TestKind.SUCC) or {}).values())
      targets += list((self.tests.get(TestKind.DIFF) or {}).values())
    else:
      targets = self.get_targets(raw_targets)

    for test in targets:
      test.begin('CLEAN')
      test.clean(self)
      test.end('CLEAN', True)

  def build(self, raw_targets: list[str]):
    targets: list[Test] = []
    if len(raw_targets) == 0:
      targets += list((self.tests.get(TestKind.SUCC) or {}).values())
      targets += list((self.tests.get(TestKind.DIFF) or {}).values())
    else:
      targets = self.get_targets(raw_targets)

    for test in targets:
      test.begin('BUILD')
      esit = test.build(self)
      test.end('BUILD', esit)
      assert esit

  def run(self, raw_targets: list[str]):
    targets: list[Test] = []
    if len(raw_targets) == 0:
      targets += list((self.tests.get(TestKind.SUCC) or {}).values())
      targets += list((self.tests.get(TestKind.DIFF) or {}).values())
    else:
      targets = self.get_targets(raw_targets)

    for test in targets:
      test.begin('RUN')
      esit = test.run(self)
      test.end('RUN', esit)
      assert esit

  def consolidate(self, raw_targets: list[str]):
    targets: list[Test] = []
    if len(raw_targets) == 0:
      targets += list((self.tests.get(TestKind.DIFF) or {}).values())
    else:
      targets = self.get_targets(raw_targets)

    for test in targets:
      test.begin('CONSOLIDATE')
      test.consolidate(self)
      test.end('CONSOLIDATE', True)

  def compare(self, raw_targets: list[str]):
    targets: list[Test] = []
    if len(raw_targets) == 0:
      targets += list((self.tests.get(TestKind.DIFF) or {}).values())
    else:
      targets = self.get_targets(raw_targets)

    for test in targets:
      test.begin('COMPARE')
      esit = test.compare(self)
      test.end('COMPARE', esit)
      assert esit

  def detect(self, raw_targets: list[str]):
    for raw_target in raw_targets:
      pieces = raw_target.split('/')
      if len(pieces) != 2:
        raise ValueError('Invalid target supplied: `%s` is not in format <kind>/<name>' % (raw_target,))
      kind, name = pieces
      if kind not in TestKind.values():
        raise ValueError('Invalid test kind in target supplied: `%s` is not a valid TestKind' % (kind,))

      if TestKind.parse(kind) not in self.tests:
        self.tests[TestKind.parse(kind)] = {}
      if name in self.tests[TestKind.parse(kind)]:
        raise ValueError('Test already discovered and in config: `%s/%s`' % (kind, name))
      namepath = os.path.join(self.test_dir, kind, name)
      test = Test.discover(namepath)
      self.tests[test.kind][test.name] = test
    self.save()

  def report(self, raw_targets: list[str]):
    targets: list[Test] = []
    if len(raw_targets) == 0:
      targets += list((self.tests.get(TestKind.SUCC) or {}).values())
      targets += list((self.tests.get(TestKind.DIFF) or {}).values())
      targets += list((self.tests.get(TestKind.FAIL) or {}).values())
    else:
      targets = self.get_targets(raw_targets)

    for test in targets:
      esit = True
      test.begin('BUILD')
      if test.kind == TestKind.FAIL:
        esit &= (not test.build(self))
      elif test.kind in [TestKind.SUCC, TestKind.DIFF]:
        esit &= test.build(self)
      test.end('BUILD', esit)
      if not esit:
        continue

      if test.kind in [TestKind.SUCC, TestKind.DIFF]:
        esit = True
        test.begin('RUN')
        esit &= test.run(self)
        test.end('RUN', esit)
      if not esit:
        continue

      if test.kind == TestKind.DIFF:
        esit = True
        test.begin('COMPARE')
        esit &= test.compare(self)
        test.end('COMPARE', esit)

def main():
  argument_parser = argparse.ArgumentParser()
  argument_parser.add_argument('-a', '--action', type=str, nargs='*', help='Actions: detect, clean, build, run, consolidate, compare, report')
  argument_parser.add_argument('-t', '--target', type=str, nargs='*', help='Targets: `<kind>/<name>`')
  argument_parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose/debug log')
  args = argument_parser.parse_args(sys.argv[1:])

  actions = (args.action or [])
  do_detect = ('detect' in actions)
  do_clean = ('clean' in actions)
  do_build = ('build' in actions)
  do_run = ('run' in actions)
  do_consolidate = ('consolidate' in actions)
  do_compare = ('compare' in actions)
  do_report = ('report' in actions)

  framework = Framework.load_from_config('config.yml')
  framework.verbose = (args.verbose or False)
  framework.restore()

  targets = (args.target or [])
  if do_detect:
    framework.detect(targets)
  if do_clean:
    framework.clean(targets)
  if do_build:
    framework.build(targets)
  if do_run:
    framework.run(targets)
  if do_consolidate:
    framework.consolidate(targets)
  if do_compare:
    framework.compare(targets)
  if do_report:
    framework.report(targets)

  framework.save()

if __name__ == '__main__':
  main()
