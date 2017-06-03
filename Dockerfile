FROM ubuntu:16.04
MAINTAINER Cap. Hindsight <hindsight@yandex.ru>

RUN \
  apt-get update && \
  apt-get install -y \
    python python-pip make git && \
  pip install --upgrade pip && \
  pip install \
    pymongo pyyaml && \
  git clone https://github.com/caphindsight/isolate && \
  cd isolate && \
  make isolate && make install && \
  apt-get install gcc g++

COPY . /testo
WORKDIR /testo
RUN \
  cp /testo/dblib/* /testo/master/ && \
  cp /testo/dblib/* /testo/worker/
