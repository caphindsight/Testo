import os
import shutil
from subprocess import Popen, PIPE

from constants import WHICH_PYTHON
from errors import GeneratorError


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
    self.test_n = kw['test_n']
    self.verdict = kw.get('verdict')
    self.points = kw.get('points')
    self.running_duration = kw.get('running_duration')
    self.memory_peak = kw.get('memory_peak')
    self.comment = kw.get('comment')
