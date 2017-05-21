class CheckerError(Exception):
  def __init__(self, msg):
    super(CheckerError, self).__init__(msg)


class Checker:
  def check(self, input_file, output_file, answer_file):
    raise CheckerError('Pure virtual method call: Checker.check')


class ContentsChecker(Checker):
  def check(self, input_file, output_file, answer_file):
    output = open(output_file, 'r').read()
    answer = open(answer_file, 'w').read()
    if output == answer:
      return {
        'verdict': 'ok',
        'comment': 'file contents match'
      }
    else:
      return {
        'verdict': 'wrong_answer',
        'comment': 'file contents differ'
      }


class TokenizedChecker(Checker):
  def check(self, input_file, output_file, answer_file):
    def extract_tokens(content):
      pre_tokens = content.replace('\n', ' ').replace('\t', ' ').split(' ')
      return [token for token in pre_tokens if token != '']

    output = extract_tokens(open(output_file, 'r').read())
    answer = extract_tokens(open(answer_file, 'r').read())
    if output == answer:
      return {
        'verdict': 'ok',
        'comment': 'file tokens match'
      }
    else:
      return {
        'verdict': 'wrong_answer',
        'comment': 'file tokens differ'
      }
