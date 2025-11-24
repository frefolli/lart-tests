from __future__ import annotations

import enum
import os
import yaml
import argparse
import sys

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

class Compiler:
  def __init__(self, path: str, include_directories: list[str]) -> None:
    self.path: str = path
    self.include_directories: list[str] = include_directories

  def to_dict(self) -> dict:
    return {
      'path': self.path,
      'include_directories': self.include_directories
    }

  @staticmethod
  def from_dict(data: dict) -> Compiler:
    return Compiler(
      path = data['path'],
      include_directories = data['include_directories'],
    )

  def compile(self, sources: list[str], links: list[str], output: str) -> int:
    cmd = CMD(self.path)
    cmd.append(['-I' + include_directory for include_directory in self.include_directories])
    cmd.append(['-l' + link for link in links])
    cmd.append(sources)
    cmd.append(['-o', output])

    print('|>', cmd.assemble())
    # return os.system(cmd.assemble())
    return 0

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
  def __init__(self, kind: TestKind, name: str, path: str, sources: list[str], links: list[str], program: str, inputs: list[str], output: str) -> None:
    self.kind: TestKind = kind
    self.name: str = name
    self.path: str = path
    self.sources: list[str] = sources
    self.links: list[str] = links
    self.program: str = program
    self.inputs: list[str] = inputs
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

    sources = []
    links = []
    inputs = []
    for file in os.listdir(path):
      ext = file.split('.')[-1]
      if ext in ['c', 'o', 'lart', 's', 'll']:
        sources.append(file)
      elif ext in ['in']:
        inputs.append('in')

    program = 'program.exe'
    output = 'program.out'
    return Test(TestKind.parse(kind), name, path, sources, links, program, inputs, output)


  def build(self, framework: Framework) -> None:
    sources = [os.path.join(self.path, source) for source in self.sources]
    c_sources = list(filter(lambda f: f.endswith('.c'), sources))
    lart_sources = list(filter(lambda f: f.endswith('.lart'), sources))
    ll_sources = list(filter(lambda f: f.endswith('.ll'), sources))
    s_sources = list(filter(lambda f: f.endswith('.s'), sources))
    o_sources = set(filter(lambda f: f.endswith('.o'), sources))

    for c_source in c_sources:
      o_source = c_source.replace('.c', '.o')
      if o_source in o_sources:
        raise ValueError('Conflicting CC::out vs LartC::in => `%s`' % (o_source,))
      o_sources.add(o_source)
      framework.cc.compile([c_source], [], o_source)

    o_sources = list(o_sources)
    sources = lart_sources + ll_sources + s_sources + o_sources
    program = os.path.join(self.path, self.program)
    framework.lartc.compile(sources, self.links, program)

  def run(self, framework: Framework) -> None:
    pass

  def clean(self, framework: Framework) -> None:
    sources = [os.path.join(self.path, source) for source in self.sources]
    c_sources = list(filter(lambda f: f.endswith('.c'), sources))
    
    o_source = [c_source.replace('.c', '.o') for c_source in c_sources]
    program = os.path.join(self.path, self.program)
    output = os.path.join(self.path, self.output)

    cmd = CMD('rm')
    cmd.append('-rf')
    cmd.append(o_source)
    cmd.append(program)
    cmd.append(output)
    print('|>', cmd.assemble())
    # os.system(cmd.assemble())

  def to_dict(self) -> dict:
    return {
      'kind': self.kind.value,
      'name': self.name,
      'path': self.path,
      'sources': self.sources,
      'links': self.links,
      'program': self.program,
      'inputs': self.inputs,
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
      inputs = (data.get('inputs') or []),
      output = (data.get('output') or 'program.out'),
    )

class Framework:
  def __init__(self, cc: Compiler, lartc: Compiler, test_dir: str) -> None:
    self.cc = cc
    self.lartc =lartc 
    self.test_dir: str = test_dir
    self.tests: dict[TestKind, list[Test]] = Framework.load_tests(test_dir)

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
        cc = Compiler('./cc', []),
        lartc = Compiler('./lartc', ['include']),
        test_dir = 'tests'
      )
      write_yaml(config_file, framework.to_dict())
      return framework

  @staticmethod
  def discover_tests(path: str) -> dict[TestKind, list[Test]]:
    tests: dict[TestKind, list[Test]] = {}
    for kinddir in os.listdir(path):
      kindpath = os.path.join(path, kinddir)
      if os.path.isdir(kindpath):
        for namedir in os.listdir(kindpath):
          namepath = os.path.join(kindpath, namedir)
          if os.path.isdir(namepath):
            test = Test.discover(namepath)
            if test.kind not in tests:
              tests[test.kind] = []
            tests[test.kind].append(test)
    return tests

  @staticmethod
  def load_tests(test_dir: str) -> dict[TestKind, list[Test]]:
    if not os.path.exists(test_dir):
      raise ValueError('Cannot load Framework as the test directory `%s` doesn\'t exist' % test_dir)
    if not os.path.isdir(test_dir):
      raise ValueError('Cannot load Framework as the test directory `%s` isn\'t a directory' % test_dir)

    test_config = os.path.join(test_dir, 'config.yml')
    if not os.path.exists(test_config):
      tests = Framework.discover_tests(test_dir)
      write_yaml(test_config, {key.value:[test.to_dict() for test in value] for (key, value) in tests.items()})
      return tests
    else:
      return {TestKind.parse(kind):[Test.from_dict(test) for test in tests] for kind, tests in read_yaml(test_config).items()}

  def clean(self):
    clean_list: list[Test] = []
    clean_list += (self.tests.get(TestKind.SUCC) or [])
    clean_list += (self.tests.get(TestKind.DIFF) or [])

    for test in clean_list:
      test.clean(self)

  def build(self):
    build_list: list[Test] = []
    build_list += (self.tests.get(TestKind.SUCC) or [])
    build_list += (self.tests.get(TestKind.DIFF) or [])

    for test in build_list:
      test.build(self)

  def run(self):
    run_list: list[Test] = []
    run_list += (self.tests.get(TestKind.SUCC) or [])
    run_list += (self.tests.get(TestKind.DIFF) or [])

    for test in run_list:
      test.run(self)

def main():
  argument_parser = argparse.ArgumentParser()
  argument_parser.add_argument('action', type=str, nargs='*', help='Actions: clean, build, run')
  args = argument_parser.parse_args(sys.argv[1:])

  do_clean = ('clean' in args.action)
  do_build = ('build' in args.action)
  do_run = ('run' in args.action)

  framework = Framework.load_from_config('config.yml')

  if do_clean:
    framework.clean()
  if do_build:
    framework.build()
  if do_run:
    framework.run()

if __name__ == '__main__':
  main()
