import base64
import logging

from checker import *
from sandbox import *


def _run_test(sandbox, test_obj, checker, limits):
  # Preparing test
  sandbox.clean('iout')
  sandbox.clean('ians')
  with sandbox.open_prepared_file('ienv/input.txt', FileMod.INPUT) as input_stream:
    input_stream.write(base64.b64decode(test_obj['input_b64']))
  with sandbox.open_prepared_file('ians/answer.txt', FileMod.INPUT) as answer_stream:
    answer_stream.write(base64.b64decode(test_obj['answer_b64']))
  prepared_input = sandbox.get_file('ienv/input.txt')
  prepared_answer = sandbox.get_file('ians/answer.txt')

  # Running solution
  sandbox.prepare_file('iout/stdout.txt', FileMod.OUTPUT)
  sandbox.prepare_file('iout/stderr.txt', FileMod.OUTPUT)
  redirects = Redirects(
    stdin='/ienv/input.txt',
    stdout='/iout/stdout.txt',
    stderr='/iout/stderr.txt',
  )
  run_res = sandbox.run('/ienv/program', redirects, limits)
  if run_res.return_code != 0:
    return {
      'verdict': 'crashed',
      'comment': run_res.isolate_stderr
    }

  # Running checker
  try:
    return checker.check(prepared_input,
        sandbox.get_file('iout/stdout.txt'), prepared_answer)
  except CheckerError, err:
    return {
      'verdict': 'checker_failure',
      'comment': err.message
    }


def run_tests(sandbox, problem_obj, solution_obj, report_cb):
  logging.info('Running tests for %s (problem %s, user %s)' %
                (solution_obj['solution'], solution_obj['problem'], solution_obj['user']))
  testsets = solution_obj.get('testsets')
  if testsets is None:
    testsets = [testset_obj['testset'] for testset_obj in problem_obj['testsets']]
  sandbox.create()
  sandbox.mount('ienv', MountOpts.READ_ONLY)
  sandbox.mount('iout', MountOpts.READ_AND_WRITE)

  with sandbox.open_prepared_file('ienv/program', FileMod.EXECUTABLE) as program_stream:
    program_stream.write(base64.b64decode(solution_obj['source_code_b64']))

  limits = Limits(
    time_limit=problem_obj['limits'].get('time_limit'),
    mem_limit=problem_obj['limits'].get('mem_limit'),
    disk_limit=problem_obj['limits'].get('disk_limit'),
    stack_limit=problem_obj['limits'].get('stack_limit'),
  )

  if problem_obj['checker'] == 'identic':
    checker = ContentsChecker()
  elif problem_obj['checker'] == 'tokenized':
    checker = TokenizedChecker()
  else:
    raise Exception('Unsupported checker: %s' % problem_obj['checker'])

  for testset_obj in problem_obj['testsets']:
    testset = testset_obj['testset']
    if testset not in testsets:
      continue
    for test_obj in testset_obj['tests']:
      test_res = _run_test(sandbox, test_obj, checker, limits)
      report_cb(testset, test_obj['test'], test_res)

  sandbox.delete()
