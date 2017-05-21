import base64
import logging
import os
import pymongo
import time
import yaml

import sandbox
import runner

def main():
  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)),
      'testo_worker.yml')
  config = yaml.load(open(config_file, 'r').read())
  mongo_client = pymongo.MongoClient(config['mongo']['address'])
  mongo_db = mongo_client[config['mongo']['database']]
  col_problems = mongo_db['problems']
  col_solutions = mongo_db['solutions']

  try:
    print 'Testo worker is now active'
    print 'Press Ctrl+C to quit'

    while True:
      solution_obj = col_solutions.find_one_and_update(
        {'status': 'queued'}, {'$set': {'status': 'compiling'}})
      if solution_obj is not None:
        solution = solution_obj['solution']
        problem = solution_obj['problem']
        problem_obj = col_problems.find_one({'problem': problem})
        compilation_resulted_in_error = False
        def compiler_cb(success, compiler_log):
          compilation_resulted_in_error = not success
          col_solutions.update_one({'solution': solution},
              {'$set':
                {'status': 'running' if success else 'compilation_error',
                 'compiler_log_b64': base64.b64encode(compiler_log)}})
        if compilation_resulted_in_error:
          return

        def report_cb(testset, test, result):
          col_solutions.update_one({'solution': solution},
              {'$set': {'results.' + testset + '.' + test: result}})
        box = sandbox.Sandbox(config['sandbox']['box_id'])
        try:
          runner.run_tests(box, problem_obj, solution_obj, compiler_cb, report_cb)
          col_solutions.update_one({'solution': solution},
              {'$set': {'status': 'ready', 'status_terminal': True}})
        except Exception, e:
          col_solutions.update_one({'solution': solution},
              {'$set': {'status': 'failed', 'status_terminal': True, 'status_description': str(e)}})
          if config['debug']:
            raise
      else:
        time.sleep(1.0)
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  main()
