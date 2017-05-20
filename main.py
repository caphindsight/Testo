import argparse
import os
from termcolor import *

from console_table import *
import loader
import runner
import sandbox
from test import Verdict


def absolute_path(relative_path):
  return os.path.join(os.getcwd(), relative_path)


class ConsoleReporter:
  def __init__(self):
    self.table = ConsoleTable([
      TableCol('test_n', 4),
      TableCol('verdict'),
      TableCol('comment'),
    ])

  def solution_starts(self, solution, problem):
    pass

  def testset_starts(self, solution, problem, testset):
    print 'Testset:', colored(testset.testset_n, attrs=['underline'])

  def test_done(self, solution, problem, testset, test, test_res):
    def colorize_verdict(verdict):
      if verdict == Verdict.OK:
        return colored('OK', 'green')
      elif verdict == Verdict.WA:
        return colored('WA', 'red')
      elif verdict == Verdict.PE:
        return colored('PE', 'cyan')
      elif verdict == Verdict.CR:
        return colored('CR', 'yellow')
      elif verdict == Verdict.TL:
        return colored('TL', 'cyan')
      elif verdict == Verdict.CF:
        return colored('CF', 'magenta')
      elif verdict == Verdict.GF:
        return colored('GF', 'magenta')

    self.table.post(
      test_n=test.test_n + '.',
      verdict=colorize_verdict(test_res.verdict),
      comment=test_res.comment,
    )

  def testset_ends(self, solution, problem, testset, testset_res):
    print

  def solution_ends(self, solution, problem, solution_res):
    pass

def run_main(args):
  assert args.lang == 'binary', 'Only \'binary\' language is supported currently.'

  print "Loading problem data.."
  problem = loader.load_problem(absolute_path(args.p))

  print "Initializing sandbox.."
  box = sandbox.Sandbox(17)
  box.create()
  rn = runner.Runner(box)
  testsets = None
  if args.t is not None:
    testsets = args.t.split(',')

  print "Running tests.."
  print

  rep = ConsoleReporter()
  rn.run_tests(problem, absolute_path(args.solution), rep, testsets)

  print "Finalizing.."
  box.delete()

def main():
  parser = argparse.ArgumentParser(
      description='Run testo locally')
  parser.add_argument('--lang', type=str, default='binary', help='programming language')
  parser.add_argument('-p', metavar='PROBLEM_DIR', type=str, help='root directory for tests')
  parser.add_argument('-t', metavar='TESTSETS', type=str, help='run only selected testsets (comma-separated)')
  parser.add_argument('solution', type=str)
  args = parser.parse_args()
  run_main(args)


if __name__ == '__main__':
  main()
