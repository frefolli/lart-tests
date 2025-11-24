from __future__ import annotations

import enum
import os
import yaml

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
    if isinstance(argx, str):
      self.args.append(argx)
    elif isinstance(argx, list):
      for arg in argx:
        assert isinstance(arg, str)
        self.args.append(arg)
    else:
      raise ValueError(argx)

  def assemble(self) -> str:
    return ' '.join([self.cmd] + self.args)

class Compiler:
  def __init__(self, path: str, include_directories: list[str]) -> None:
    self.path: str = path
    self.include_directories: list[str] = include_directories

  def compile(self, sources: list[str], links: list[str], output: str) -> int:
    cmd = CMD(self.path)
    cmd.append(['-I' + include_directory for include_directory in self.include_directories])
    cmd.append(['-l' + link for link in links])
    cmd.append(sources)
    cmd.append(['-o', output])

    print('|>', cmd.assemble())
    # return os.system(cmd.assemble())
    return 0

class Framework:
  def __init__(self) -> None:
    self.cc = Compiler('./cc', [])
    self.lartc = Compiler('./lartc', ['include'])

class TestKind(enum.Enum):
  SUCC='succ'
  DIFF='diff'
  FAIL='fail'

  @staticmethod
  def values() -> list[str]:
    return [_.value for _ in list(TestKind)]

class Test:
  def __init__(self, kind: TestKind, name: str, path: str, sources: list[str], links: list[str], program: str, inputs: list[str]) -> None:
    self.kind: TestKind = kind
    self.name: str = name
    self.path: str = path
    self.sources: list[str] = sources
    self.links: list[str] = links
    self.program: str = program
    self.inputs: list[str] = inputs

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
    return Test(TestKind(kind), name, path, sources, links, program, inputs)


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

  def to_dict(self) -> dict:
    return {
      'kind': self.kind.value,
      'name': self.name,
      'path': self.path,
      'sources': self.sources,
      'links': self.links,
      'program': self.program,
      'inputs': self.inputs,
    }

  def from_dict(self, data: dict) -> Test:
    return Test(
      kind = TestKind(data['kind']),
      name = data['name'],
      path = data['path'],
      sources = (data['sources'] or []),
      links = (data['links'] or []),
      program = (data['program'] or 'program.exe'),
      inputs = (data['inputs'] or []),
    )

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

def main():
  framework = Framework()

  tests: dict[TestKind, list[Test]] = {}
  test_config = './tests/config.yml'
  if not os.path.exists(test_config):
    tests = discover_tests('./tests')
    write_yaml(test_config, {key.value:[test.to_dict() for test in value] for (key, value) in tests.items()})
  else:
    read_yaml(test_config)

if __name__ == '__main__':
  main()
