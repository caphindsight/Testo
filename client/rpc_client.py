import argparse
import base64
import sys
from termcolor import *
import yaml
import xmlrpclib

from console_table import *
import problem_utils


COMMANDS = {
  'help': 'Show this help message.',
  'problem': 'Manage problem database.',
  'run': 'Run solution against prepared tests.'
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
  _ = parser.parse_args(args)

  source_code_b64 = base64.b64encode(open(_.solution, 'r').read())
  id = stub.run({
    'language': _.l,
    'problem': _.p,
    'source_code_b64': source_code_b64,
    'testsets': _.t
  })
  print id

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
