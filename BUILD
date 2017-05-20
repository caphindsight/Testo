py_library(
  name='testo_lib',
  srcs=glob(['testo_lib/*.py']),
)

py_binary(
  name='testo',
  srcs=glob(['client/*.py']),
  main='client/rpc_client.py',
  data=['client/testo_client.yml'],
  deps=[':testo_lib'],
)

py_binary(
  name='master',
  srcs=glob(['orchestrator/*.py']),
  main='orchestrator/orchestrator.py',
  data=['orchestrator/testo_orchestrator.yml'],
  deps=[':testo_lib'],
)

py_binary(
  name='worker',
  srcs=glob(['worker/*.py']),
  main='worker/worker.py',
  data=['worker/testo_worker.yml'],
  deps=[':testo_lib'],
)
