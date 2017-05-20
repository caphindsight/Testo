import os
import yaml

from errors import *
from checker import *
from model import *
from sandbox import Limits
from testset import *


def load_problem(problem_dir):
  problem_n = os.path.basename(problem_dir)
  config_file = os.path.join(problem_dir, problem_n + '.yml')
  problem_yaml = yaml.load(open(config_file, 'r').read())
  title = problem_yaml['title']

  if problem_yaml['checker'] == 'identical':
    checker = ContentsChecker()
  elif problem_yaml['checker'] == 'tokenized':
    checker = TokenizedChecker()
  else:
    raise ConfigError('Unsupported checker type: %s' % problem_yaml['checker'])

  global_limits = Limits(
    time_limit = problem_yaml['limits'].get('time_limit'),
    mem_limit = problem_yaml['limits'].get('mem_limit'),
    disk_limit = problem_yaml['limits'].get('disk_limit'),
    stack_limit = problem_yaml['limits'].get('stack_limit'),
  )

  testsets = []
  for testset_yaml in problem_yaml['testsets']:
    testset_n = testset_yaml['testset']
    testset_dir = os.path.join(problem_dir, testset_n)
    if testset_yaml['type'] == 'prepared':
      tests_data = []
      for f in os.listdir(testset_dir):
        inp = os.path.join(testset_dir, f)
        ans = inp + '.a'
        if os.path.isfile(inp) and os.path.isfile(ans):
          tests_data.append((f, inp, ans))
      tests_data.sort(key=lambda td: td[0])
      testset = PreparedTestSet(testset_n, tests_data)
    else:
      raise ConfigError('Unsupported testset type: %s' % testset_yaml['type'])

    testsets.append(testset)

  return Problem(
    problem_n=problem_n,
    title=title,
    checker=checker,
    global_limits=global_limits,
    testsets=testsets,
  )
