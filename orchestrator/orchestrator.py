import os
import pymongo
import xmlrpclib
import yaml
from SimpleXMLRPCServer import SimpleXMLRPCServer

from service import RpcService


def main():
  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)),
      'testo_orchestrator.yml')
  print config_file
  config = yaml.load(open(config_file, 'r').read())
  mongo_client = pymongo.MongoClient(config['mongo']['address'])
  mongo_db = mongo_client[config['mongo']['database']]

  service = RpcService(mongo_db)
  server = SimpleXMLRPCServer((config['orchestrator_rpc']['addr'], config['orchestrator_rpc']['port']),
      logRequests=config['orchestrator_rpc']['log_requests'])
  server.register_instance(service)
  try:
    print ('Testo orchestrator RPC server is listening on http://%s:%s/' %
                (config['orchestrator_rpc']['addr'], config['orchestrator_rpc']['port']))
    print 'Press Ctrl+C to quit'
    server.serve_forever()
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  main()
