FROM ubuntu:16.04
MAINTAINER Cap. Hindsight <hindsight@yandex.ru>

RUN \
  apt-get update && \
  apt-get install -y \
    git python python-pip make && \
  pip install --upgrade pip && \
  pip install \
    pymongo pyyaml && \
  git clone https://github.com/caphindsight/isolate && \
  cd isolate && \
  make isolate && make install && \
  apt-get install gcc g++

COPY . /testo_worker
WORKDIR /testo_worker
CMD python worker.py
