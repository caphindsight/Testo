from SimpleXMLRPCServer import SimpleXMLRPCServer
import pymongo
import yaml
import xmlrpclib

from worker.service import WorkerService

def main():
  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)),
      'testo_worker.yml')
  config = yaml.load(open(config_file, 'r').read())
  mongo_client = pymongo.MongoClient(config['mongo']['address'])
  mongo_db = mongo_client[config['mongo']['database']]

  testing_thread = TestingThread(mongo_db, config['sandbox']['box_id'],
      max_queue_len=config['queue']['max_len'])
  testing_thread.start_thread()

  service = WorkerService(mongo_db, testing_thread)

  server = SimpleXMLRPCServer((config['worker_rpc']['addr'], config['worker_rpc']['port']),
      logRequests=config['worker_rpc']['log_requests'])
  server.register_instance(service)

  try:
    print 'Testo worker RPC server is listening on http://%s:%s/' %
          (config['worker_rpc']['addr'], config['worker_rpc']['port'])
    print 'Press Ctrl+C to quit'
    server.serve_forever()
  except KeyboardInterrupt:
    testing_thread.stop_thread()
    print 'Bye!'


if __name__ == '__main__':
  main()
