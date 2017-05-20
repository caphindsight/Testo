class Problem:
  def __init__(self, **kw):
    self.problem_n = kw.get('problem_n')
    self.title = kw.get('title')
    self.statement = kw.get('statement')
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
