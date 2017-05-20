from test import PreparedTest, GeneratedTest


class TestSet:
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
