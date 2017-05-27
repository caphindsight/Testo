import argparse
import base64
import datetime
import os
import random
import sys
from termcolor import *
from time import sleep
import yaml
import xmlrpclib

from console_table import *
import problem_utils


COMMANDS = {
  'help': 'Show this help message.',

  'browse': 'Browse database collection.',
  'lookup': 'Lookup object in the database collection.',
  'insert': 'Insert object in the database collection.',
  'update': 'Update object in the database collection.',
  'drop': 'Delete object from the database collection.',
  'cleanup': 'Clean up old objects in the database collection.',

  'problem': 'Helper command to upload and download problems.'
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
  return os.path.abspath(os.path.join(os.getcwd(), path))

def _basename_noext(path):
  bn = os.path.basename(path)
  return os.path.splitext(bn)[0]

def _ext(path):
  bn = os.path.basename(path)
  return os.path.splitext(bn)[1]

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

def _parse_datetime(unix_time):
  return datetime.datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')


def subcmd_help(args, stub, auth):
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


def subcmd_browse(args, stub, auth):
  parser = _parser('browse')
  parser.add_argument('-f', '-i', '--include', action='append', dest='fields',
      help='Fields to include in the response, e.g. -f user -f admin ...')
  parser.add_argument('-q', '--query', action='append', dest='query',
      help='Query only specific values, e.g. -q user=user1 ...')
  parser.add_argument('-w', '--width', type=int, default=0, dest='width',
      help='Output table width (defaults to terminal width).')
  parser.add_argument('collection', metavar='COLLECTION', type=str,
      help='Collection to browse.')
  _ = parser.parse_args(args)
  if _.fields is None:
    _fail('Please provide fields to browse for.')
  if _.query is None:
    _.query = dict()
  else:
    query = dict()
    for q in _.query:
      arr = q.split(':')
      key = arr[0]
      val = ':'.join(arr[1:])
      query[key] = _parse_kval(val)
    _.query = query
  data = stub.db_browse(auth, _.collection, _.query, _.fields)
  table = ConsoleTable([TableCol(field, 10) for field in _.fields])
  table.fit_width(_.width)
  fields_dict = dict()
  for field in _.fields:
    fields_dict[field] = field
  table.post_header(**fields_dict)
  for item in data:
    if item.has_key('created'):
      item['created'] = _parse_datetime(item['created'])
    if item.has_key('last_update'):
      item['last_update'] = _parse_datetime(item['last_update'])
    table.post(**item)


def subcmd_lookup(args, stub, auth):
  parser = _parser('lookup')
  parser.add_argument('-i', '--include', action='append', dest='include_fields',
      help='Fields to include in the response, e.g. -i user -i admin ...')
  parser.add_argument('-e', '--exclude', action='append', dest='exclude_fields',
      help='Fields to exclude from response, e.g. -e token ...')
  parser.add_argument('collection', metavar='COLLECTION', type=str,
      help='Collection to lookup from.')
  parser.add_argument('id', metavar='ID', type=str,
      help='Object identifier')
  _ = parser.parse_args(args)
  projection = _.include_fields
  data = stub.db_lookup(auth, _.collection, _.id, projection)
  if _.exclude_fields is None:
    _.exclude_fields = []
  for ef in _.exclude_fields:
    del data[ef]
  sys.stdout.write(yaml.dump(data, default_flow_style=False))


def _parse_kval(val):
  if val == 'TRUE':
    val = True
  elif val == 'FALSE':
    val = False
  elif val.startswith('INT_'):
    val = int(val[4:])
  elif val.startswith('LIST_'):
    val = val[5:].split(',')
  elif val.startswith('RAND_'):
    n = int(val[5:])
    val = str(2 ** n + random.getrandbits(n))
  return val


def subcmd_insert(args, stub, auth):
  parser = _parser('insert')
  parser.add_argument('--yaml', metavar='DATA_FILE', default='',
      help='Insert object from yaml data file.')
  parser.add_argument('-i', '-p', '--property', metavar='NAME:VALUE', action='append', dest='properties',
      help='Set object property.')
  parser.add_argument('--rand', action='store_true',
      help='Use random object identifier.')
  parser.add_argument('--rm', action='store_true',
      help='Remove object before inserting on id collision (please consider using update instead).')
  parser.add_argument('collection', metavar='COLLECTION', type=str,
      help='Collection to insert into.')
  parser.add_argument('id', metavar='ID', type=str, default='',
      help='Object identifier.')
  _ = parser.parse_args(args)
  obj = {}
  if _.yaml != '':
    obj = yaml.loads(open(_abs_path(_.yaml), 'r').read())
  if _.properties is None:
    _.properties = []
  for prop in _.properties:
    arr = prop.split(':')
    key = arr[0]
    val = ':'.join(arr[1:])
    obj[key] = _parse_kval(val)
  if _.rand:
    stub.db_insert_with_random_id(auth, _.collection, obj)
  else:
    if _.id == '':
      _fail('Please do one of the following:\n  Provide the object identifier.\n  Enable the --rand flag to generate object id at runtime')
    if _.rm:
      try:
        stub.db_drop(auth, _.collection, _.id)
      except:
        pass
    stub.db_insert(auth, _.collection, _.id, obj)


def subcmd_update(args, stub, auth):
  parser = _parser('update')
  parser.add_argument('-i', '-p', '--property', metavar='NAME:VALUE', action='append', dest='properties',
      help='Set object property.')
  parser.add_argument('collection', metavar='COLLECTION', type=str,
      help='Collection to update.')
  parser.add_argument('id', metavar='ID', type=str, default='',
      help='Object identifier.')
  _ = parser.parse_args(args)
  updates = {}
  if _.properties is None:
    _fail('Nothing to update.')
  for prop in _.properties:
    arr = prop.split(':')
    key = arr[0]
    val = ':'.join(arr[1:])
    updates[key] = _parse_kval(val)
  stub.db_update(auth, _.collection, _.id, updates)


def subcmd_drop(args, stub, auth):
  parser = _parser('drop')
  parser.add_argument('collection', metavar='COLLECTION', type=str,
      help='Collection to drop from.')
  parser.add_argument('id', metavar='ID', type=str, default='',
      help='Object identifier.')
  _ = parser.parse_args(args)
  stub.db_drop(auth, _.collection, _.id)


def subcmd_cleanup(args, stub, auth):
  parser = _parser('cleanup')
  parser.add_argument('--secs', metavar='SECS', type=float, default=0,
      help='Seconds until expired.')
  parser.add_argument('--mins', metavar='SECS', type=float, default=0,
      help='Minutes until expired.')
  parser.add_argument('--hrs', metavar='SECS', type=float, default=0,
      help='Hours until expired.')
  parser.add_argument('--days', metavar='SECS', type=float, default=0,
      help='Days until expired.')
  parser.add_argument('collection', metavar='COLLECTION', type=str,
      help='Collection to clean up.')
  _ = parser.parse_args(args)
  timespan_secs = 0
  if _.secs > 0:
    timespan_secs += int(_.secs)
  if _.mins > 0:
    timespan_secs += int(_.mins * 60)
  if _.hrs > 0:
    timespan_secs += int(_.hrs * 60 * 60)
  if _.days > 0:
    timespan_secs += int(_.days * 60 * 60 * 24)
  if timespan_secs == 0:
    _fail('Please provide one of the followind: --secs, --mins, --hrs, --days')
  cleanup_res = stub.db_cleanup(auth, _.collection, timespan_secs)
  print 'Cleaned up objects:', cleanup_res['deleted_count']


def subcmd_problem(args, stub, auth):
  parser = _parser('problem')
  parser.add_argument('--upload', action='store_true',
      help='Upload a problem from local directory to the database.')
  parser.add_argument('--download', action='store_true',
      help='Download a problem from the database to a local directory.')
  parser.add_argument('dir', metavar='DIR', type=str,
      help='Local directory path.')
  _ = parser.parse_args(args)
  directory = _abs_path(_.dir)
  problem_name = os.path.basename(directory)
  if _.upload + _.download != 1:
    _fail('Exactly one action from (--push, --pull) has to be specified')
  if _.upload:
    obj = problem_utils.load_problem(directory)
    try:
      stub.db_drop(auth, 'problems', problem_name)
    except:
      pass
    stub.db_insert(auth, 'problems', problem_name, obj)
  elif _.download:
    obj = stub.db_lookup(auth, 'problems', problem_name, None)
    problem_utils.save_problem(obj, directory)


def main():
  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)),
      'testo_client.yml')
  config = yaml.load(open(config_file, 'r').read())
  stub = xmlrpclib.ServerProxy(config['server_addr'], allow_none=True)
  args = sys.argv
  auth = config['auth']
  progname = args.pop(0)
  if len(args) == 0:
    subcmd_help(args, stub, auth)
  else:
    subcmd = args.pop(0)
    func = globals().get('subcmd_' + subcmd)
    if not func:
      subcmd_help(args, stub, auth)
      exit(1)
    else:
      func(args, stub, auth)

if __name__ == '__main__':
  try:
    main()
  except xmlrpclib.Fault, f:
    print colored(str(f), 'red')
    exit(10)
