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
    if user not in contest_obj['contestants']:
      raise AccessDeniedException('User %s doesn\'t have access to contest %s' % (user, contest))
    if task not in contest_obj['tasks']:
      raise AccessDeniedException('Unknown task %s' % task)
    solution_obj = {
      'user': user,
      'contest': contest,
      'task': task,
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
    if solution_obj.get('user') != user:
      raise AccessDeniedException('Solution %s was submitted by another person' % solution)
    return solution_obj

  def clock(self, shift_secs):
    return int(time.time()) + shift_secs
