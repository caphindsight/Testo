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
  'clock': 'Lookup server wall clock.',

  'browse': 'Browse database collection.',
  'lookup': 'Lookup object in the database collection.',
  'insert': 'Insert object in the database collection.',
  'update': 'Update object in the database collection.',
  'drop': 'Delete object from the database collection.',
  'cleanup': 'Clean up old objects in the database collection.',

  'problem': 'Helper command for uploading and downloading problems data.',
  'consolidate': 'Helper command for consolidating last accepted solutions in the contest.',

  'submit': 'Submit solution for a contest task.',
  'monitor': 'Monitor your solution results.',
  'scorings': 'Monitor contest scoring.',
}

def _parser(command):
  return argparse.ArgumentParser(
    prog='testo ' + command,
    description=COMMANDS[command]
  )

def _fail(message):
  print message
  exit(1)

def _concat(a, b):
  if a is None:
    return None
  if b is None:
    return a
  return a + b

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


def subcmd_clock(args, stub, auth):
  parser = _parser('clock')
  parser.add_argument('--secs', metavar='SECS', type=float, default=0,
      help='Seconds shift.')
  parser.add_argument('--mins', metavar='SECS', type=float, default=0,
      help='Minutes shift.')
  parser.add_argument('--hrs', metavar='SECS', type=float, default=0,
      help='Hours shift.')
  parser.add_argument('--days', metavar='SECS', type=float, default=0,
      help='Days shift.')
  _ = parser.parse_args(args)
  shift_secs = 0
  if _.secs > 0:
    shift_secs += int(_.secs)
  if _.mins > 0:
    shift_secs += int(_.mins * 60)
  if _.hrs > 0:
    shift_secs += int(_.hrs * 60 * 60)
  if _.days > 0:
    shift_secs += int(_.days * 60 * 60 * 24)
  utime = stub.clock(shift_secs)
  print 'Shift:', shift_secs, 'secs'
  print 'Unix time:', utime
  print 'Time string:', _parse_datetime(utime)


def _walk(obj, path):
  if path == '':
    return None
  p = path.split('.')
  def step(obj, part):
    if type(obj) == list:
      ind = int(part)
      if ind >= 0 and ind < len(obj):
        return obj[ind]
      else:
        return None
    elif type(obj) == dict:
      return obj.get(part)
  for part in p:
    obj = step(obj, part)
  return obj


def subcmd_browse(args, stub, auth):
  parser = _parser('browse')
  parser.add_argument('-f', '-i', '--include', action='append', dest='fields',
      help='Fields to include in the response, e.g. -f user -f admin ...')
  parser.add_argument('-q', '--query', action='append', dest='query',
      help='Query only specific values, e.g. -q user=user1 ...')
  parser.add_argument('-z', '--quiet-field', action='append', dest='quiet_fields',
      help='Receive this field but do not show in the table.')
  parser.add_argument('--sort-by', dest='sort_by', default='',
      help='Field to sort by.')
  parser.add_argument('--descending', action='store_true',
      help='Sort descending')
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
  if _.quiet_fields == None:
    _.quiet_fields = []
  data = stub.db_browse(auth, _.collection, _.query, _.fields + _.quiet_fields)
  table = ConsoleTable([TableCol(field, 10) for field in _.fields])
  table.fit_width(_.width)
  fields_dict = dict()
  for field in _.fields:
    fields_dict[field] = field
  table.post_header(**fields_dict)
  data.sort(key=lambda it: _walk(it, _.sort_by))
  if _.descending:
    data.reverse()
  for item in data:
    if item.has_key('created'):
      item['created'] = _parse_datetime(item['created'])
    if item.has_key('last_update'):
      item['last_update'] = _parse_datetime(item['last_update'])
    tablerow = {}
    for field in _.fields:
      tablerow[field] = _walk(item, field)
    table.post(**tablerow)


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
  if val == 'NONE':
    val = None
  elif val == 'TRUE':
    val = True
  elif val == 'FALSE':
    val = False
  elif val.startswith('INT:'):
    val = int(val[4:])
  elif val.startswith('LIST:'):
    val = val[5:].split(',')
  elif val.startswith('RAND:'):
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
    obj = yaml.load(open(_abs_path(_.yaml), 'r').read())
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


def _colored_verdict(verdict):
  if verdict == 'ok':
    return colored('OK', 'green', attrs=['bold'])
  elif verdict == 'skipped':
    return colored('--', 'magenta', attrs=['dark'])
  elif verdict == 'wrong_answer':
    return colored('WA', 'red', attrs=['bold'])
  elif verdict == 'presentation_error':
    return colored('PE', 'cyan', attrs=['bold'])
  elif verdict == 'idle':
    return colored('IL', 'blue', attrs=['bold'])
  elif verdict == 'crash' or verdict == 'crashed':
    return colored('CR', 'yellow', attrs=['bold'])
  elif verdict == 'runtime_error':
    return colored('RE', 'yellow', attrs=['bold'])
  elif verdict == 'security_violation':
    return colored('SV', 'yellow', attrs=['bold'])
  elif verdict == 'timeouted':
    return colored('TO', 'blue', attrs=['bold'])
  elif verdict == 'out_of_memory':
    return colored('OM', 'blue', attrs=['bold'])
  elif verdict == 'out_of_disk':
    return colored('OD', 'blue', attrs=['bold'])
  elif verdict == 'out_of_stack':
    return colored('OS', 'blue', attrs=['bold'])
  elif verdict == 'generator_failure':
    return colored('GF', 'magenta', attrs=['bold'])
  elif verdict == 'checker_failure':
    return colored('CF', 'magenta', attrs=['bold'])
  else:
    return colored('??', attrs=['bold'])


def _monitor_solution(stub, auth, id):
  tests_console_table = ConsoleTable([
    TableCol('testn', 4, AlignMode.RIGHT),
    TableCol('verdict'),
    TableCol('time', 7),
    TableCol('mem', 9),
    TableCol('comment', 20),
  ])
  status = ''
  while True:
    solution_obj = stub.monitor(auth, id)
    if solution_obj['status_terminal'] == True:
      break
    if solution_obj['status'] != status:
      status = solution_obj['status']
      print 'Submission status:', colored(status, attrs=['bold'])
  if solution_obj['status'] == 'compilation_error':
    print 'Submission status:', colored('compilation_error', 'red', attrs=['dark'])
    print base64.b64decode(solution_obj['compiler_log_b64'])
  elif solution_obj['status'] == 'failed':
    print 'Submission status:', colored('compilation_error', 'magenta', attrs=['dark'])
    print solution_obj['status_description']
  elif solution_obj['status'] == 'ready':
    print 'Submission status:', colored('ready', 'green', attrs=['dark'])
    testsets = solution_obj.get('testsets')
    if testsets is None:
      testsets = sorted([ts for ts in solution_obj['results']['testsets']])
    for testset in testsets:
      print
      print 'Tests from testset:', colored(testset, attrs=['underline'])
      tests = solution_obj['results']['testsets'][testset]['tests']
      for test in sorted(list(tests)):
        tests_console_table.post(
          testn=test + '.',
          verdict=_colored_verdict(tests[test]['verdict']),
          time=_concat(tests[test]['runtime'].get('time'), 's'),
          mem=_concat(tests[test]['runtime'].get('max-rss'), 'kb'),
          comment=tests[test]['comment']
        )
        if tests[test]['verdict'] != 'skipped':
          sleep(0.2)
      verdict = solution_obj['results']['testsets'][testset]['verdict']
      verdict_good = verdict in ['accepted', 'max_score']
      testset_result = colored(verdict, 'green' if verdict_good else 'red',
          attrs=['bold' if verdict_good else 'dark'])
      print 'Testset result:', testset_result
    verdict = solution_obj['results']['verdict']
    verdict_good = verdict in ['accepted', 'max_score']
    solution_result = colored(verdict, 'green' if verdict_good else 'red',
        attrs=['bold' if verdict_good else 'dark'])
    solution_points = solution_obj['results'].get('points')
    if len(testsets) > 1:
      print
      print 'Solution result:', solution_result
    if solution_points is not None:
      if len(testsets) == 1:
        print
      print 'Solution points:', solution_points
  else:
    print ('Unknown status: %s' % solution_obj['status'])


def subcmd_submit(args, stub, auth):
  parser = _parser('submit')
  parser.add_argument('-c', '--contest', metavar='CONTEST', type=str, dest='contest',
      help='Contest name, can also be inferred from the source code file name.')
  parser.add_argument('-t', '--task', metavar='TASK', type=str, dest='task',
      help='Task name, can also be inferred from the source code file name.')
  parser.add_argument('-l', '--lang', metavar='LANG', type=str, dest='lang',
      help='Programming language in which your program is written.')
  parser.add_argument('source_code', metavar='SOURCE_CODE',
      help='Solution source code file.')
  parser.add_argument('--detached', action='store_true',
      help='Detached mode: only print the submission id and exit.')
  _ = parser.parse_args(args)

  source_code = _abs_path(_.source_code)
  try:
    contest = _.contest if _.contest is not None else '_'.join(_basename_noext(source_code).split('_')[:-1])
    task = _.task if _.task is not None else _basename_noext(source_code).split('_')[-1]
  except IndexError:
    _fail('Unable to infer contest and task from source code file name')
  language = _.lang if _.lang is not None else _detect_language(_ext(source_code))
  source_code_b64 = base64.b64encode(open(source_code, 'r').read())
  solution = stub.submit(auth, contest, task, language, source_code_b64)
  if _.detached:
    print solution['solution']
  else:
    print 'Submitting solution..'
    _monitor_solution(stub, auth, solution['solution'])


def subcmd_consolidate(args, stub, auth):
  parser = _parser('consolidate')
  parser.add_argument('-c', '--contest', metavar='CONTEST', type=str, dest='contest',
      help='Contest name.')
  _ = parser.parse_args(args)

  contest_obj = stub.db_lookup(auth, 'contests', _.contest, None)
  if contest_obj.get('consolidated') == True:
    _fail('Contest already consolidated')
  contestants = set(contest_obj['contestants'])
  tasks_to_problems = dict()
  for task in contest_obj['tasks']:
    tasks_to_problems[task] = contest_obj['tasks'][task]['problem']

  solution_objs = stub.db_browse(auth, 'solutions',
      {'contest': _.contest, 'results.verdict': 'accepted', 'live_submit': True},
      ['solution', 'contest', 'created', 'language', 'results',
       'source_code_b64', 'task', 'user']
  )

  buckets = dict()
  collected_count = 0
  for solution_obj in solution_objs:
    solution_user = solution_obj['user']
    if solution_user not in contestants:
      continue
    solution_task = solution_obj['task']
    if solution_task not in tasks_to_problems:
      continue
    bucket_key = (solution_user, solution_task)
    if bucket_key not in buckets:
      buckets[bucket_key] = []
    buckets[bucket_key].append(solution_obj)
    collected_count += 1

  print ('Collected %s solutions.' % collected_count)

  buckets_size = len(buckets)
  buckets_covered = 0

  for bucket_key in buckets:
    progress = float(buckets_covered) / float(buckets_size)
    print ('Progress: %s%%..' % int(progress * 100))
    buckets[bucket_key].sort(key=lambda x: -x['created'])
    sol = buckets[bucket_key][0]
    user = sol['user']
    task = sol['task']
    sleep(0.5)
    print
    print 'Contestant:', colored(user, 'white', attrs=['bold'])
    print 'Task:', colored(task, 'white', attrs=['bold']) + ',', tasks_to_problems.get(task)
    consolidation_testsets = contest_obj['tasks'][task].get('consolidation_testsets')
    if consolidation_testsets is None:
      consolidation_testsets = []
    new_solution = stub.db_insert_with_random_id(auth, 'solutions', {
      'user': user,
      'contest': sol['contest'],
      'task': task,
      'problem': tasks_to_problems.get(task),
      'testsets': consolidation_testsets,
      'scoring': 'quantitative',
      'language': sol['language'],
      'source_code_b64': sol['source_code_b64'],
      'status': 'queued',
      'status_terminal': False,
    })
    _monitor_solution(stub, auth, new_solution)
    new_solution_obj = stub.db_lookup(auth, 'solutions', new_solution, None)
    points = new_solution_obj['results'].get('points')
    if points is None:
      points = 0
    stub.db_update(auth, 'contests', _.contest, {
      'scorings.' + user + '.' + task + '.consolidated_solution': new_solution,
      'scorings.' + user + '.' + task + '.results': new_solution_obj['results'],
      'scorings.' + user + '.' + task + '.points': points,
    })
  stub.db_update(auth, 'contests', _.contest, {'consolidated': True})
  print
  print
  print 'Done!'


def subcmd_monitor(args, stub, auth):
  parser = _parser('monitor')
  parser.add_argument('-c', '--contest', metavar='CONTEST', type=str, dest='contest',
      help='Contest name.')
  parser.add_argument('-t', '--task', metavar='TASK', dest='task',
      help='Task name.')
  _ = parser.parse_args(args)
  scorings_entry = stub.get_scorings_entry(auth, _.contest, _.task)
  solution = scorings_entry['consolidated_solution']
  _monitor_solution(solution)


def subcmd_scorings(args, stub, auth):
  parser = _parser('scorings')
  parser.add_argument('-c', '--contest', metavar='CONTEST', type=str, dest='contest',
      help='Contest name.')
  parser.add_argument('-w', '--width', type=int, default=0, dest='width',
      help='Output table width (defaults to terminal width).')
  _ = parser.parse_args(args)
  res = stub.get_scorings(auth, _.contest)
  scorings = res['scorings']
  tasks = res['tasks']

  scorings_table_cols = [
    TableCol('rank', 5),
    TableCol('contestant', 20),
  ]
  scoring_table_header = {
    'rank': '#',
    'contestant': 'contestant',
    'total': '=',
  }
  for task in tasks:
    scorings_table_cols.append(TableCol(task, 5))
    scoring_table_header[task] = task
  scorings_table_cols.append(TableCol('total', 5))

  scorings_table = ConsoleTable(scorings_table_cols)
  scorings_table.fit_width(_.width)
  scorings_table.post_header(**scoring_table_header)

  for i in scorings:
    raw = {
      'rank': str(i['rank']) + '.',
      'contestant': i['contestant'],
      'total': i['total_points']
    }
    for task in tasks:
      raw[task] = i['task_points'][task]
    scorings_table.post(**raw)


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
