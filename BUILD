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
