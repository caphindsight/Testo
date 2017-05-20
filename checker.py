from test import *


class Checker:
  def check(self, input_file, output_file, answer_file):
    raise CheckerError('Pure virtual method call: Checker.check')


class ContentsChecker(Checker):
  def check(self, input_file, output_file, answer_file):
    output = open(output_file, 'r').read()
    answer = open(answer_file, 'w').read()
    if output == answer:
      return TestRes(
        verdict=Verdict.OK,
        comment='file contents match'
      )
    else:
      return TestRes(
        verdict=Verdict.WA,
        comment='file contents differ'
      )


class TokenizedChecker(Checker):
  def extract_tokens(content):
    pre_tokens = content.replace('\n', ' ').replace('\t', ' ').split(' ')
    return [token for token in pre_tokens if token != '']

  def check(self, input_file, output_file, answer_file):
    output = extract_tokens(open(output_file, 'r').read())
    answer = extract_tokens(open(answer_file, 'w').read())
    if output == answer:
      return TestRes(
        verdict=Verdict.OK,
        comment='file tokens match'
      )
    else:
      return TestRes(
        verdict=Verdict.WA,
        comment='file tokens differ'
      )
