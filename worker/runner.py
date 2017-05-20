from workers.checker import *
from workers.errors import *
from workers.model import *
from workers.sandbox import *


def _run_test(sandbox, test, checker, limits):
  sandbox.clean('iout')
  sandbox.clean('ians')
  prepared_input = sandbox.get_file('ienv/input.txt')
  prepared_answer = sandbox.get_file('ians/answer.txt')

  # Generating test data
  try:
    test.prepare_test(prepared_input, prepared_answer)
  except GeneratorError, err:
    return TestRes(
      test_n=test.test_n,
      verdict=Verdict.GF,
      comment=err.message,
    )

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
    return TestRes(
      test_n=test.test_n,
      verdict=Verdict.CR,
      comment=run_res.isolate_stderr,
    )

  # Running checker
  try:
    chk_res = checker.check(prepared_input,
        sandbox.get_file('iout/stdout.txt'), prepared_answer)
    chk_res.test_n = test.test_n
    return chk_res
  except CheckerError, err:
    return TestRes(
      test_n=test.test_n,
      verdict=Verdict.CF,
      comment=err.message,
    )


class Runner:
  def __init__(self, sandbox):
    self.sandbox = sandbox

  def run_tests(self, problem, program, reporter, testsets=None):
    reporter.solution_starts(problem)
    if testsets is None:
      testsets = [i.testset_n for i in problem.testsets]
    self.sandbox.create()
    self.sandbox.mount('ienv', MountOpts.READ_ONLY)
    self.sandbox.mount('iout', MountOpts.READ_AND_WRITE)
    self.sandbox.copy_file(program, 'ienv/program', FileMod.EXECUTABLE)
    testset_results = []
    for testset in problem.testsets:
      individual_results = []
      if testset.testset_n not in testsets:
        continue
      reporter.testset_starts(problem, testset)
      limits = Limits.merge(problem.global_limits, testset.limits)
      for test in testset.tests():
        test_res = _run_test(self.sandbox, test, problem.checker, limits)
        individual_results.append(test_res)
        reporter.test_done(problem, testset, test, test_res)

      testset_res = TestSetRes(testset.testset_n, individual_results)
      testset_results.append(testset_res)
      reporter.testset_ends(problem, testset, testset_res)

    solution_res = SolutionRes(testset_results)
    reporter.solution_ends(problem, solution_res)
    self.sandbox.delete()
    return solution_res