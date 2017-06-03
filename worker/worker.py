import base64
import logging
import os
import pymongo
import time
import yaml

from manager import *
from users_manager import *

import sandbox
import runner


class DbManager:
  def __init__(self, db):
    self.db = db
    self.users = UsersManager(db['users'])
    self.problems = Manager(db['problems'], 'problem')
    self.solutions = Manager(db['solutions'], 'solution')


def process_solution(db_manager, solution_obj):
  solution = solution_obj.get('solution')
  if solution is None:
    return

  problem = solution_obj.get('problem')
  if problem is None:
    db_manager.solutions.update(solution, {
      'status': 'failed',
      'status_terminal': True,
      'status_description': 'Problem not specified',
    })
    return

  problem_obj = db_manager.problems.lookup(problem)
  if problem_obj is None:
    db_manager.solutions.update(solution, {
      'status': 'failed',
      'status_terminal': True,
      'status_description': ('Problem %s not found' % problem),
    })
    return

  box = sandbox.Sandbox(config['sandbox']['box_id'])

  try:
    def compiler_cb(success, compiler_log):
      if success:
        db_manager.solutions.update(solution, {
          'status': 'running',
          'status_terminal': False,
          'compiler_log_b64': base64.b64encode(compiler_log),
        })
      else:
        db_manager.solutions.update(solution, {
          'status': 'compilation_error',
          'status_terminal': True,
          'compiler_log_b64': base64.b64encode(compiler_log),
        })
    def report_cb(testset, test, result):
      db_manager.solutions.update(solution, {
        'results.testsets.' + testset + '.tests.' + test: result,
      })
    def testset_cb(testset, testset_verdict, points=None, test_verdict=None, testn=None):
      db_manager.solutions.update(solution, {
        'results.testsets.' + testset + '.verdict': testset_verdict,
        'results.testsets.' + testset + '.points': points,
        'results.testsets.' + testset + '.test_verdict': test_verdict,
        'results.testsets.' + testset + '.failed_test': testn,
      })
    def success_cb(solution_verdict, points=None):
      db_manager.solutions.update(solution, {
        'status': 'ready',
        'status_terminal': True,
        'results.verdict': solution_verdict,
        'results.points': points,
      })
    runner.run_tests(box, problem_obj, solution_obj, compiler_cb, report_cb, testset_cb, success_cb)
  except Exception, e:
    db_manager.solutions.update(solution, {
      'status': 'failed',
      'status_terminal': True,
      'status_description': str(e),
    })


def main():
  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)),
      'testo_worker.yml')
  config = yaml.load(open(config_file, 'r').read())
  mongo_client = pymongo.MongoClient(config['mongo']['address'])
  mongo_db = mongo_client[config['mongo']['database']]
  db_manager = DbManager(mongo_db)
  try:
    print 'Testo worker is now active'
    print 'Press Ctrl+C to quit'

    while True:
      try:
        solution_obj = db_manager.db['solutions'].find_one_and_update(
          {'status': 'queued'},
          {'$set': {'status': 'preparing', 'status_terminal': False}}
        )
        if solution_obj is not None:
          process_solution(db_manager, solution_obj)
        else:
          time.sleep(1.0)
      except KeyboardInterrupt:
        raise
      except Exception, e:
        print str(e)
        if config['debug']:
          raise
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  main()
