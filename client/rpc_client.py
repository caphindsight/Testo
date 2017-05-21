import argparse
import base64
import os
import sys
from termcolor import *
import time
import yaml
import xmlrpclib

from console_table import *
import problem_utils


COMMANDS = {
  'help': 'Show this help message.',
  'problem': 'Manage problem database.',
  'run': 'Run solution against prepared tests.',
}

def _parser(command):
  return argparse.ArgumentParser(
    prog='testo ' + command,
    description=COMMANDS[command]
  )


def _fail(message):
  print message
  exit(1)


def _abs_path(path):
  return os.path.join(os.getcwd(), path)


def _basename_noext(path):
  bn = os.path.basename(path)
  return os.path.splitext(bn)[0]


def _ext(path):
  bm = os.path.basename(path)
  return ps.path.splitext(bn)[1]


def _detect_language(ext):
  lang_map = {
    '.cc': 'cxx11',
    '.c++': 'cxx11',
    '.cpp': 'cxx11',
    '.cxx': 'cxx11',
  }
  res = lang_map.get(ext)
  if res is None:
    _fail('Unrecognized language extension: %s' % ext)
  return res


def subcmd_help(args, stub):
  print 'usage: testo COMMAND [ARGS ...]'
  print
  print 'Testo testing system client.'
  print
  print 'Commands:'
  commands_table = ConsoleTable([
    TableCol('command', 15),
    TableCol('description')
  ])
  for command in sorted(list(COMMANDS)):
    commands_table.post(command=' ' + command, description=COMMANDS[command])


def subcmd_problem(args, stub):
  parser = _parser('problem')
  parser.add_argument('--list', action='store_true',
      help='List existing problems.')
  parser.add_argument('--push', action='store_true',
      help='Push a problem from local directory to the database.')
  parser.add_argument('--pull', action='store_true',
      help='Pull a problem from the database to a local directory.')
  parser.add_argument('--drop', action='store_true',
      help='Drop a problem from the database.')
  parser.add_argument('-p', metavar='PROBLEM', type=str,
      help='Problem name, if applicable.')
  parser.add_argument('--dir', metavar='DIRECTORY', type=str,
      help='Local directory to save/load problem data, if applicable.')
  _ = parser.parse_args(args)
  if _.list + _.push + _.pull + _.drop != 1:
    _fail('Exactly one action from (--list, --push, --pull, --drop) has to be specified')
  if _.list:
    table = ConsoleTable([
      TableCol('problem', 15),
      TableCol('title')
    ])
    problems = stub.problem_list()
    for problem in problems:
      table.post(problem=problem['problem'], title=problem['title'])
  elif _.push:
    if _.dir is None: _fail('--dir must be specified.')
    obj = problem_utils.load_problem(_abs_path(_.dir))
    stub.problem_push(obj)
  elif _.pull:
    if _.p is None: _fail('-p must be specified.')
    if _.dir is None: _fail('--dir must be specified.')
    obj = stub.problem_pull(_.p)
    problem_utils.save_problem(obj, _abs_path(_.dir))
  elif _.drop:
    if _.p is None: _fail('-p must be specified.')
    stub.problem_drop(_.p)


TESTS_CONSOLE_TABLE = ConsoleTable([
  TableCol('testn', 4, AlignMode.RIGHT),
  TableCol('verdict'),
  TableCol('comment', 20),
])


def _colored_verdict(verdict):
  if verdict == 'ok':
    return colored('OK', 'green')
  elif verdict == 'wrong_answer':
    return colored('WA', 'red')
  elif verdict == 'presentation_error':
    return colored('PE', 'cyan')
  elif verdict == 'idle':
    return colored('IL', 'blue')
  elif verdict == 'crash' or verdict == 'crashed':
    return colored('CR', 'yellow')
  elif verdict == 'security_violation':
    return colored('SV', 'yellow')
  elif verdict == 'timeouted':
    return colored('TO', 'blue')
  elif verdict == 'out_of_memory':
    return colored('OM', 'blue')
  elif verdict == 'out_of_disk':
    return colored('OD', 'blue')
  elif verdict == 'out_of_stack':
    return colored('OS', 'blue')
  elif verdict == 'generator_failure':
    return colored('GF', 'magenta')
  elif verdict == 'checker_failure':
    return colored('CF', 'magenta')
  else:
    return '??'


def _report_tests(tests):
  for test in sorted(list(tests)):
    TESTS_CONSOLE_TABLE.post(
      testn=test + '.',
      verdict=_colored_verdict(tests[test]['verdict']),
      comment=tests[test]['comment']
    )
    time.sleep(0.3)


def _report_testset(testset):
  print
  print 'Tests from testset:', colored(testset, attrs=['underline'])


def _monitor_solution(stub, id):
  terminate = False
  reported_testsets = dict()
  current_testset = ''
  while not terminate:
    solution_obj = stub.monitor(id)
    terminate = solution_obj['status_terminal']
    new_testsets = dict()
    for testset in solution_obj['testsets']:
      if not reported_testsets.has_key(testset):
        reported_testsets[testset] = dict()
      testset_obj = solution_obj['testsets'][testset]
      for test in testset_obj:
        if not reported_testsets[testset].has_key(test):
          if not new_testsets.has_key(testset):
            new_testsets[testset] = dict()
          new_testsets[testset][test] = new_testsets[testset][test]
    if current_testset in new_testsets:
      _report_tests(new_testsets[current_testset])
      del new_testsets[current_testset]
    for testset in new_testsets:
      _report_testset(testset)
      _report_tests(new_testsets[testset])
      current_testset = testset
    if terminate:
      if solution_obj['status'] == 'compilation_error':
        print 'Solution status:', colored('compilation error', 'red')
        print base64.b64decode(solution_obj['compiler_log_b64'])
      elif solution_obj['status'] == 'failed':
        print 'Testing system error:', solution_obj['status_description']


def subcmd_run(args, stub):
  parser = _parser('run')
  parser.add_argument('-p', metavar='PROBLEM', type=str,
      help='Problem name, can also be inferred from the source code file name.')
  parser.add_argument('-t', metavar='TESTSETS', type=str,
      help='Testsets to run on. Comma-separated. By default covers all testsets.')
  parser.add_argument('-l', metavar='LANG', type=str,
      help='Programming language in which your program is written.')
  parser.add_argument('solution', metavar='SOLUTION',
      help='Solution source code file.')
  parser.add_argument('-d', action='store_true',
      help='Detached mode: only print the submission id and exit.')
  _ = parser.parse_args(args)

  solution = _abs_path(_.solution)
  problem = _.p if _.p is not None else _basename_noext(solution)
  language = _.l if _.l is not None else _detect_language(_ext(solution))
  source_code_b64 = base64.b64encode(open(solution, 'r').read())
  testsets = _.t.split(',') if _.t is not None else None
  id = stub.run({
    'language': language,
    'problem': problem,
    'source_code_b64': source_code_b64,
    'testsets': testsets
  })

  if _.d:
    print id
  else:
    _monitor_solution(stub, id)


def main():
  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)),
      'testo_client.yml')
  config = yaml.load(open(config_file, 'r').read())
  stub = xmlrpclib.ServerProxy(config['server_addr'])
  args = sys.argv
  progname = args.pop(0)
  if len(args) == 0:
    subcmd_help(args, stub)
  else:
    subcmd = args.pop(0)
    func = globals().get('subcmd_' + subcmd)
    if not func:
      subcmd_help(args, stub)
      exit(1)
    else:
      func(args, stub)

if __name__ == '__main__':
  try:
    main()
  except xmlrpclib.Fault, f:
    print colored(str(f), 'red')
    exit(10)
