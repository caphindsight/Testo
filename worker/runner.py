import base64
import logging

from checker import *
import compiler_utils
from sandbox import *


VERDICTS_BY_STATUSES = {
  'TO': 'timeouted',
  'RE': 'runtime_error',
  'SG': 'segfaulted',
}


def _verdict_by_status(status):
  res = VERDICTS_BY_STATUSES.get(status)
  if res is None:
    return 'crashed'
  else:
    return res


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
      'verdict': _verdict_by_status(run_res.meta.get('status')),
      'runtime': run_res.meta,
      'comment': run_res.isolate_stderr,
      'points': 0,
    }

  # Running checker
  try:
    chk_res = checker.check(prepared_input,
        sandbox.get_file('iout/stdout.txt'), prepared_answer)
    chk_res['runtime'] = run_res.meta
    return chk_res
  except CheckerError, err:
    return {
      'verdict': 'checker_failure',
      'runtime': run_res.meta,
      'comment': err.message,
      'points': 0,
    }


def run_tests(sandbox, problem_obj, solution_obj, compiler_cb, report_cb, testset_cb, success_cb):
  qualitative_scoring = solution_obj.get('scoring') == 'qualitative'

  sandbox.create()
  try:
    logging.info('Running tests for %s (problem %s, user %s)' %
                  (solution_obj['solution'], solution_obj['problem'], solution_obj['user']))
    testsets = solution_obj.get('testsets')
    if testsets is None:
      testsets = [testset_obj['testset'] for testset_obj in problem_obj['testsets']]
    sandbox.mount('ienv', MountOpts.READ_ONLY)
    sandbox.mount('iout', MountOpts.READ_AND_WRITE)

    language = solution_obj['language']
    ext = compiler_utils.file_extension(language)
    with sandbox.open_prepared_file('ienv/program' + ext, FileMod.INPUT) as program_stream:
      program_stream.write(base64.b64decode(solution_obj['source_code_b64']))

    compiler_res = compiler_utils.compile(sandbox,
        sandbox.get_file('ienv/program' + ext), sandbox.get_file('ienv/program'), language)
    compiler_cb(compiler_res.success, compiler_res.compiler_log)
    if not compiler_res.success:
      return

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

    solution_rejected = False
    scored_points = 0
    max_points = problem_obj.get('max_points')

    for testset_obj in problem_obj['testsets']:
      testset = testset_obj['testset']
      points_per_test = testset_obj.get('points_per_test')
      max_points_per_testset = testset_obj.get('max_points')
      if points_per_test is None:
        points_per_test = 0

      scored_points_per_testset = 0

      if testset not in testsets:
        continue
      rejected = False
      for test_obj in testset_obj['tests']:
        if rejected and qualitative_scoring:
          test_res = {
            'verdict': 'skipped',
            'runtime': {},
            'comment': 'test was skipped',
            'points': 0,
          }
        else:
          test_res = _run_test(sandbox, test_obj, checker, limits)
          if test_res['verdict'] == 'ok':
            test_res['points'] = points_per_test
            scored_points_per_testset += points_per_test
          else:
            test_res['points'] = 0
            rejected = True
            if qualitative_scoring:
              testset_cb(testset, 'rejected', None, test_res['verdict'], test_obj['test'])
        report_cb(testset, test_obj['test'], test_res)
      if not rejected and max_points_per_testset is not None:
        scored_points_per_testset = max_points_per_testset
      scored_points += scored_points_per_testset
      if qualitative_scoring:
        if not rejected:
          testset_cb(testset, 'accepted')
      else:
        if not rejected:
          testset_cb(testset, 'max_score', scored_points_per_testset)
        else:
          testset_cb(testset, 'partial_score', scored_points_per_testset)
      if rejected:
        solution_rejected = True
    if qualitative_scoring:
      success_cb('accepted' if not solution_rejected else 'rejected', None)
    else:
      if not solution_rejected and max_points is not None:
        scored_points = max_points
      success_cb('max_score' if not solution_rejected else 'partial_score', scored_points)
  finally:
    sandbox.delete()
