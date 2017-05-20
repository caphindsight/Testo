import argparse
import sys
from termcolor import *
import yaml
import xmlrpclib

from testo_lib.console_table import *


COMMANDS = {
  'help': 'Show this help message.',
  'problem': 'Manage problem database.',
}

def _parser(command):
  return argparse.ArgumentParser(
    prog='testo ' + command,
    description=COMMANDS[command]
  )


def _fail(message):
  print message
  exit(1)


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
  parser.add_argument('directory', metavar='DIRECTORY', type=str, nargs='?')
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
    _fail('Pushing problems is not implemented yet')
  elif _.pull:
    _fail('Pulling problems is not implemented yet')
  elif _.drop:
    stub.problem_drop(_.directory)

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
