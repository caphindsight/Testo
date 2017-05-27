import pymongo
import random
import time


class RecordNotFoundException(Exception):
  def __init__(self, id_field, id_value):
    super(RecordNotFoundException, self).__init__(
        'Record not found: %s \'%s\'' % (id_field, id_value))
    self.id_field = id_field
    self.id_value = id_value


class DuplicateRecordIndex(Exception):
  def __init__(self, id_field, id_value):
    super(RecordNotFoundException, self).__init__(
        'Record already exists: %s \'%s\'' % (id_field, id_value))
    self.id_field = id_field
    self.id = id_value


class Manager(object):
  def __init__(self, collection, id_field):
    self.collection = collection
    self.id_field = id_field
    self.collection.create_index(
        [(self.id_field, pymongo.ASCENDING)], unique=True)

  def browse(self, query={}, projection=None):
    cur = self.collection.find(query, projection=projection)
    res = []
    for i in cur:
      obj = i.copy()
      del obj['_id']
      res.append(obj)
    return res

  def lookup(self, id, projection=None):
    obj = self.collection.find_one({self.id_field: id}, projection=projection)
    if obj is None:
      raise RecordNotFoundException(self.id_field, id)
    del obj['_id']
    return obj

  def generate_random_id(self):
    prefix = self.id_field + '_'
    randpart = str(2 ** 100 + random.getrandbits(100))
    postfix = str(int(time.time() * 1000000))
    return prefix + randpart + postfix

  def insert(self, id, obj):
    obj = obj.copy()
    obj[self.id_field] = id
    obj['type'] = self.id_field
    current_time = int(time.time())
    obj['created'] = current_time
    obj['last_update'] = current_time
    try:
      self.collection.insert_one(obj)
    except pymongo.errors.DuplicateKeyError:
      raise DuplicateRecordIndex(self.id_field, id)

  def insert_with_random_id(self, obj):
    id = self.generate_random_id()
    self.insert(id, obj)
    return id

  def update(self, id, updates, upsert=False):
    upd = self.collection.find_one_and_update(
        {self.id_field: id},
        {'$set': dict(updates, last_update=int(time.time()))},
        upsert=upsert)
    if not upsert and (upd is None or len(upd) == 0):
      raise RecordNotFoundException(self.id_field, id)

  def drop(self, id):
    der = self.collection.delete_one({self.id_field: id})
    if der.deleted_count == 0:
      raise RecordNotFoundException(self.id_field, id)

  def cleanup(self, timespan_secs):
    utime = time.time() - timespan_secs
    der = self.collection.delete_many({'last_update': {'$lt': utime}})
    return {
      'deleted_count': der.deleted_count
    }
