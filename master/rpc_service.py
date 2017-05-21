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

  def problem_push(self, data):
    self.col_problems.find_one_and_update(
        {'problem': data['problem']}, {'$set': data}, upsert=True)

  def problem_drop(self, problem):
    res = self.col_problems.delete_one({'problem': problem})
    if res.deleted_count != 1:
      raise Exception('Found %s problems matching the drop request' % res.deleted_count)

  def run(self, args):
    id = _rand_id()
    solution_obj = {
      'language': args['language'],
      'problem': args['problem'],
      'status': 'queued',
      'solution': id,
      'source_code_b64': args['source_code_b64'],
      'testsets': args['testsets'],
      'user': 'default_user'
    }
    self.col_solutions.insert_one(solution_obj)
    return id

  def contest_list(self):
    result = []
    for contest in self.col_contests.find():
      result.append({
        'contest': contest['contest'],
        'title': contest['title'],
        'schedule': contest['schedule'],
        'policy': contest['policy']
      })
    return result

  def contest_pull(self, contest):
    return _doc_body(self.col_contests.find_one({'contest': contest}))

  def contest_push(self, data):
    self.col_contests.find_one_and_update(
        {'contest': data['contest']}, {'$set': data}, upsert=True)
