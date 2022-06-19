FROM ubuntu:focal
USER root

############################################
# get base OS up to date
############################################

RUN apt update
RUN apt -yq dist-upgrade
RUN apt -yq autoremove

############################################
# tzdata first to avoid timezone prompt
############################################

RUN apt install -yq tzdata

#######################

WORKDIR /home/root
ENV BASEDIR=/home/root

RUN useradd -ms /bin/bash focal

USER focal
ENV USER focal
WORKDIR /home/focal


