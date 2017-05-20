from worker.errors import *

class Problem:
  def __init__(self, **kw):
    self.problem_n = kw.get('problem_n')
    self.title = kw.get('title')
    self.checker = kw.get('checker')
    self.global_limits = kw.get('global_limits')
    self.testsets = kw.get('testsets')


class Solution:
  def __init__(self, **kw):
    self.problem_n = kw.get('problem_n')
    self.user = kw.get('user')
    self.submitted_by = kw.get('submitted_by')
    self.language = kw.get('language')


class SolutionRes:
  def __init__(self, testset_results):
    self.testset_results = testset_results


class Test(object):
  def __init__(self, test_n):
    self.test_n = test_n

  def prepare_test(self, prepared_input, prepared_answer):
    raise GeneratorError('Pure virtual method call: Test.prepare_test')


class PreparedTest(Test):
  def __init__(self, test_n, input_file, answer_file):
    super(PreparedTest, self).__init__(test_n)
    self.input_file = input_file
    self.answer_file = answer_file

  def prepare_test(self, prepared_input, prepared_answer):
    if not os.path.isfile(self.input_file):
      raise GeneratorError('Test input file not found: "%s"' % self.input_file)
    shutil.copyfile(self.input_file, prepared_input)
    os.chmod(prepared_input, FileMod.INPUT)
    if not os.path.isfile(self.answer_file):
      raise GeneratorError('Test answer file not found: "%s"' % self.answer_file)
    shutil.copyfile(self.answer_file, prepared_answer)


class GeneratedTest(Test):
  def __init__(self, test_n, generator_script):
    super(PreparedTest, self).__init__(test_n)
    self.generator_script = generator_script

  def prepare_test(self, prepared_input, prepared_answer):
    r = Popen(
      [WHICH_PYTHON, self.generator_script, self.test_n,
       prepared_input, prepared_answer],
      stdin=PIPE, stdout=PIPE, stderr=PIPE
    ).wait()

    if r.returncode != 0:
      raise GeneratorError('Generator script failure',
          return_code=r.returncode, stdout=r.stdout().read())


class Verdict:
  OK = 'ok'
  WA = 'wrong_answer'
  PE = 'presentation_error'
  CR = 'crash'
  TL = 'time_limit_exceeded'
  CF = 'checker_failure'
  GF = 'generator_failure'


class TestRes:
  def __init__(self, **kw):
    self.test_n = kw.get('test_n')
    self.verdict = kw.get('verdict')
    self.points = kw.get('points')
    self.running_duration = kw.get('running_duration')
    self.memory_peak = kw.get('memory_peak')
    self.comment = kw.get('comment')


class TestSet(object):
  def __init__(self, testset_n, limits=None):
    self.testset_n = testset_n
    self.limits = limits

  def tests(self):
    pass


class PreparedTestSet(TestSet):
  def __init__(self, testset_n, tests_data, limits=None):
    super(PreparedTestSet, self).__init__(testset_n, limits)
    self.tests_data = tests_data

  def tests(self):
    for (test_n, input_file, answer_file) in self.tests_data:
      yield PreparedTest(test_n, input_file, answer_file)


class GeneratedTestSet(TestSet):
  def __init__(self, testset_n, generator_script, tests_count, limits=None):
    super(GeneratedTestSet, self).__init__(testset_n, limits)
    self.generator_script = generator_script
    self.tests_count = tests_count

  def tests(self):
    width = len(str(self.tests_count))
    for i in range(1, self.tests_count + 1):
      test_n = '0' * (width - len(str(i))) + str(i)
      yield GeneratedTest(test_n, generator_script)


class TestSetRes:
  def __init__(self, testset_n, individual_results):
    self.testset_n = testset_n
    self.individual_results = individual_results
