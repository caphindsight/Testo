py_binary(
  name='testo',
  srcs=glob(['client/*.py']),
  main='client/rpc_client.py',
  data=['client/testo_client.yml'],
)

py_binary(
  name='testo_master',
  srcs=glob(['master/*.py']),
  main='master/master.py',
  data=['master/testo_master.yml'],
)

py_binary(
  name='testo_worker',
  srcs=glob(['worker/*.py']),
  main='worker/worker.py',
  data=['worker/testo_worker.yml'],
)
