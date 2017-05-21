import pymongo
import random


def _rand_id():
  return str(random.getrandbits(256))


def _doc_body(doc):
  del doc['_id']
  return doc


class RpcService:
  def __init__(self, db):
    self.db = db
    self.col_contests = db['contests']
    self.col_problems = db['problems']
    self.col_solutions = db['solutions']

  def problem_list(self):
    result = []
    for problem in self.col_problems.find():
      result.append({
        'problem': problem['problem'],
        'title': problem['title']
      })
    return result

  def problem_pull(self, problem):
    return _doc_body(self.col_problems.find_one({'problem': problem}))

  def problem_push(self, problem_obj):
    self.col_problems.find_one_and_update(
        {'problem': problem_obj['problem']}, {'$set': problem_obj}, upsert=True)

  def problem_drop(self, problem):
    res = self.col_problems.delete_one({'problem': problem})
    if res.deleted_count != 1:
      raise Exception('Found %s problems matching the drop request' % res.deleted_count)

  def run(self, solution_obj):
    id = _rand_id()
    solution_doc = {
      'language': solution_obj['language'],
      'problem': solution_obj['problem'],
      'status': 'queued',
      'status_terminal': False,
      'solution': id,
      'source_code_b64': solution_obj['source_code_b64'],
      'testsets': solution_obj['testsets'],
      'user': 'default_user'
    }
    self.col_solutions.insert_one(solution_doc)
    return id

  def monitor(self, solution):
    solution_obj = self.col_solutions.find_one({'solution': solution})
    if solution_obj is None:
      return None
    else:
      return _doc_body(solution_obj)
