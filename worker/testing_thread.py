import base64
import os
import logging
import shutil
from threading import Thread
from tempdir import mkdtemp
from time import sleep

from testo_lib import problem_utils
from worker import loader
from worker.runner import *
from worker.sandbox import *


def _doc_body(doc):
  del doc['_id']
  return doc


def _run_thread(thread):
  while not thread.stop_requested:
    try:
      try:
        (solution, testsets) = thread.queue.pop(0)
      except IndexError:
        sleep(0.1)
        continue

      solution = thread.col_solutions.find_one_and_update({'solution': solution},
          {'$set': {'status': 'running'}})

      problem = solution['problem']
      problem_obj = _doc_body(thread.col_problems.find_one({'probem': problem}))
      tempdir = mkdtemp()
      problem_utils.save_problem(problem_obj, tempdir)
      problem_dir = os.path.join(tempdir, problem)
      program = os.path.join(tempdir, 'program')
      with open(program, 'w') as program_stream:
        program_stream.write(base64.b64decode(solution['source_code_b64']))
      problem_data = loader.load_problem(problem_dir)

      class MongoReporter:
        def solution_starts(self, problem):
          pass
        def testset_starts(self, problem, testset):
          pass
        def testset_ends(self, problem, testset, testset_res):
          pass
        def solution_ends(self, problem, solution_res):
          pass
        def test_done(self, problem, testset, test, test_res):
          prefix = 'results.%s.%s.' % (testset.testset_n, test.test_n)
          thread.col_solutions.find_one_and_update({'solution': solution},
              {'$set': {
                prefix + 'verdict': test_res.verdict,
                prefix + 'comment': test_res.comment,
              }})

      runner.run_tests(problem_data, program, MongoReporter(), testsets)
      shutil.rmtree(tempdir)
    except Exception, e:
      logging.error(str(e))


class TestingThread:
  def __init__(self, db, sandbox_id, max_queue_len=None):
    self.db = db
    self.col_solutions = db['solutions']
    self.col_problems = db['problems']
    self.sandbox = Sandbox(sandbox_id)
    self.runner = Runner(self.sandbox)
    self.max_queue_len = max_queue_len
    self.thread = Thread(target=_run_thread, args=(self,))
    self.queue = []
    self.stop_requested = False

  def start_thread(self):
    self.thread.start()

  def stop_thread(self):
    self.stop_requested = True
    self.thread.join()

  def enqueue(solution, testsets=None):
    if self.max_queue_len is not None and len(self.queue) >= self.max_queue_len:
      raise Exception('This worker is overwhelmed')
    self.queue.append((solution, testsets))
