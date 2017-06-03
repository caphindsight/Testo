FROM ubuntu:16.04
MAINTAINER Cap. Hindsight <hindsight@yandex.ru>

RUN \
  apt-get update && \
  apt-get install -y \
    python python-pip make && \
  pip install --upgrade pip && \
  pip install \
    pymongo pyyaml

COPY . /testo
WORKDIR /testo
RUN \
  cp /testo/dblib/* /testo/master/ && \
  cp /testo/dblib/* /testo/worker/
