FROM ubuntu:16.04
MAINTAINER Cap. Hindsight <hindsight@yandex.ru>

RUN \
  apt-get update && \
  apt-get install -y \
    git python python-pip make && \
  pip install --upgrade pip && \
  pip install \
    termcolor pymongo pyyaml && \
  git clone https://github.com/caphindsight/isolate && \
  cd isolate && \
  make isolate && make install

COPY . /worker
WORKDIR /worker
CMD python worker.py
