FROM ubuntu:jammy
USER root

############################################
# get base OS up to date
############################################

RUN apt update
RUN apt -yq dist-upgrade
RUN apt -yq autoremove
RUN apt install -yq wget mkisofs gcc g++ make zlib1g-dev vim
RUN apt install -yq libgmp-dev libmpfr-dev mpc lbzip2 bzip2

############################################
# tzdata first to avoid timezone prompt
############################################

RUN apt install -yq tzdata

#######################

ADD setup.sh /home/root/setup.sh
ADD fetch.sh /home/root/fetch.sh

WORKDIR /home/root
ENV BASEDIR=/home/root
ENV PATH="${PATH}:/usr/local/psxsdk/bin"

RUN /home/root/fetch.sh
RUN /home/root/setup.sh

RUN useradd -ms /bin/bash ps1dev

RUN mkdir /home/ps1dev/examples

RUN cp -r /home/root/source/psxsdk-20180115/examples/* /home/ps1dev/examples/
#RUN cp /home/root/source/psxsdk-20180115/Makefile.cfg /home/ps1dev/
RUN chown -R ps1dev.ps1dev /home/ps1dev

USER ps1dev
ENV USER ps1dev
WORKDIR /home/ps1dev

