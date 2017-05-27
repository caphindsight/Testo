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

  def db_browse(self, auth, collection, projection):
    self.users.authorize_admin(auth['user'], auth['token'])
    manager = self._get_manager(collection)
    return manager.browse(projection)

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
