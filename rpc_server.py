import pymongo
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

from constants import *
from rpc_service import RpcService


def main():
  client = pymongo.MongoClient(MONGO_ADDRESS)
  service = RpcService(client[MONGO_DATABASE])
  server = SimpleXMLRPCServer(('0.0.0.0', RPC_SERVER_PORT),
      logRequests=True, allow_none=True)
  server.register_instance(service)
  try:
    print 'RPC server is listening on http://0.0.0.0:%s/..' % RPC_SERVER_PORT
    print 'Press Ctrl+C to quit'
    server.serve_forever()
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  main()
