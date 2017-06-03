import pymongo
import random

from manager import *
from users_manager import *


class UnsupportedCollectionException(Exception):
  def __init__(self, collection):
    super(UnsupportedCollectionException, self).__init__(
        'Unsupported collection: \'%s\'' % collection)
    self.collection = collection


class RpcService:
  def __init__(self, db):
    self.db = db
    self.users = UsersManager(db['users'])
    self.managers = {'users': self.users}
    self.contests = self._manager('contests', 'contest')
    self.problems = self._manager('problems', 'problem')
    self.solutions = self._manager('solutions', 'solution')

  def _manager(self, collection_name, id_field):
    manager = Manager(self.db[collection_name], id_field)
    self.managers[collection_name] = manager
    return manager

  def _get_manager(self, collection):
    manager = self.managers.get(collection)
    if manager is None:
      raise UnsupportedCollectionException(collection)
    return manager

  def db_browse(self, auth, collection, query, projection):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.browse(query, projection)

  def db_lookup(self, auth, collection, id, projection):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.lookup(id, projection)

  def db_insert(self, auth, collection, id, obj):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.insert(id, obj)

  def db_insert_with_random_id(self, auth, collection, obj):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.insert_with_random_id(obj)

  def db_update(self, auth, collection, id, updates, upsert=False):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.update(id, updates, upsert=upsert)

  def db_drop(self, auth, collection, id):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.drop(id)

  def db_cleanup(self, auth, collection, timespan_secs):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.cleanup(timespan_secs)

  def submit(self, auth, contest, task, language, source_code_b64):
    self.users.authorize(auth['user'], auth['token'])
    user = auth['user']
    contest_obj = self.contests.lookup(contest)
    schedule = contest_obj.get('schedule')
    now = int(time.time())
    if schedule is not None:
      if now < schedule['start']:
        raise AccessDeniedException('Contest %s starts in %s minutes' % (contest, (schedule['start'] - now) / 60))
      if now > schedule['finish']:
        raise AccessDeniedException('Contest %s is finished' % contest)
    if contest_obj.get('consolidated') == True:
      raise AccessDeniedException('Contest %s has been consolidated' % contest)
    if user not in contest_obj['contestants']:
      raise AccessDeniedException('User %s doesn\'t have access to contest %s' % (user, contest))
    if task not in contest_obj['tasks']:
      raise AccessDeniedException('Unknown task %s' % task)
    solution_obj = {
      'user': user,
      'contest': contest,
      'task': task,
      'live_submit': True,
      'problem': contest_obj['tasks'][task]['problem'],
      'testsets': contest_obj['tasks'][task].get('testsets'),
      'scoring': contest_obj['tasks'][task].get('scoring'),
      'language': language,
      'source_code_b64': source_code_b64,
      'status': 'queued',
      'status_terminal': False,
    }
    id = self.solutions.insert_with_random_id(solution_obj)
    return {
      'solution': id
    }

  def monitor(self, auth, solution):
    self.users.authorize(auth['user'], auth['token'])
    user = auth['user']
    solution_obj = self.solutions.lookup(solution)
    if not self.users.is_admin(user) and solution_obj.get('user') != user:
      raise AccessDeniedException('Solution %s was submitted by another person' % solution)
    return solution_obj

  def get_scorings_entry(self, auth, contest, task):
    self.users.authorize(auth['user'], auth['token'])
    user = auth['user']
    is_admin = self.users.is_admin(user)
    contest_obj = self.contests.lookup(contest)
    if not is_admin and user not in contest_obj['contestants']:
      raise AccessDeniedException('User %s doesn\'t have access to contest %s' % (user, contest))
    if task not in contest_obj['tasks']:
      raise AccessDeniedException('Task %s not found in contest %s' % (task, contest))
    scorings = contest_obj['scorings']
    if user not in scorings:
      raise AccessDeniedException('Your solution hasn\'t been consolidated yet')
    if task not in scorings[user]:
      raise AccessDeniedException('Your solution hasn\'t been consolidated yet')
    return scorings[task]

  def get_scorings(self, auth, contest):
    self.users.authorize(auth['user'], auth['token'])
    user = auth['user']
    is_admin = self.users.is_admin(user)
    contest_obj = self.contests.lookup(contest)
    if contest_obj['consolidated'] != True:
      raise AccessDeniedException('Contest was not consolidated yet')
    if not is_admin and user not in contest_obj['contestants']:
      raise AccessDeniedException('User %s doesn\'t have access to contest %s' % (user, contest))
    scorings = []
    for contestant in contest_obj['scorings']:
      entry = {
        'contestant': contestant,
        'total_points': 0,
        'task_points': dict(),
      }
      for task in contest_obj['tasks']:
        res = contest_obj['scorings'][contestant].get(task)
        if res is not None:
          entry['task_points'][task] = res['points']
          entry['total_points'] += res['points']
        else:
          entry['task_points'][task] = 0
      scorings.append(entry)
    sort(scorings, key=lambda x: -x['total_points'])
    for i in xrange(len(scorings)):
      scorings[i]['rank'] = i + 1
    return {
      'scorings': scorings,
      'tasks': list(contest_obj['tasks']),
    }

  def clock(self, shift_secs):
    return int(time.time()) + shift_secs
