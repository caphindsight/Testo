import pymongo


class WorkerService:
  def __init__(self, db, testing_thread):
    self.db = db
    self.col_solutions = db['solutions']
    self.testing_thread = testing_thread

  def enqueue(self, sid):
    pass

  def monitor(self, sid):
    pass
