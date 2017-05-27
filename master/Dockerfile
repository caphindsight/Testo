FROM ubuntu:16.04
MAINTAINER Cap. Hindsight <hindsight@yandex.ru>

RUN \
  apt-get update && \
  apt-get install -y \
    python python-pip make && \
  pip install --upgrade pip && \
  pip install \
    pymongo pyyaml

COPY . /testo_master
WORKDIR /testo_master
CMD python master.py
