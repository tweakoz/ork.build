FROM ubuntu:jammy
USER root

############################################
# get base OS up to date
############################################

RUN apt update
RUN apt -y dist-upgrade
RUN apt -y autoremove

############################################
# tzdata first to avoid timezone prompt
############################################

RUN apt install -yq tzdata

############################################

RUN apt install -yq python3 python3-pip pkg-config libcairo2-dev openssh-client
RUN apt install -yq git git-lfs wget curl aha
RUN apt install -yq imagemagick cmake libreadline-dev libxcb-xfixes0-dev
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

############################################
# ??? TODO - get rid of SUDO 
############################################

RUN apt install -yq sudo 

############################################
# pips required by workers
############################################

RUN pip3 install yarl gitpython pycairo
RUN pip3 install transitions jsonpickle hashfs
RUN pip3 install zmq sshtunnel

############################################

RUN apt -y autoremove

############################################
# OBT install system deps
############################################

ADD --chown=root:root --chmod=676 ./container-scripts/obt.ix.installdeps.ubuntu22.py /root/installdeps.py
RUN /root/installdeps.py

############################################
# as workerub22 user
############################################

RUN useradd -p workerub22 -G sudo -ms /bin/bash workerub22
RUN passwd -d workerub22
USER workerub22
ENV USER workerub22
WORKDIR /home/workerub22

############################################
# fetch github key
############################################

RUN mkdir -p ~/.ssh
RUN --mount=type=secret,id=ssh_public,uid=1000 --mount=type=secret,id=ssh_private,uid=1000 ssh-agent bash -c 'ssh-add /run/secrets/ssh_private; ssh-keyscan -H github.com >> ~/.ssh/known_hosts'

############################################

ADD --chown=workerub22:workerub22 "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

############################################
# copy worker implementation files
############################################

ADD --chown=workerub22:workerub22 --chmod=700 ci_impl/*.py /home/workerub22/
ADD --chown=workerub22:workerub22 --chmod=700 ci_impl/*.sh /home/workerub22/
ADD --chown=workerub22:workerub22 --chmod=666 ci_impl/*.svg /home/workerub22/

############################################
# final worker setup
############################################

ADD --chown=workerub22:workerub22 worker22.json /home/workerub22/worker.json

ADD --chown=workerub22:workerub22 --chmod=700 container-scripts/start-worker.sh /home/workerub22/
ADD --chown=workerub22:workerub22 --chmod=700 container-scripts/spin.sh /home/workerub22/
ADD --chown=workerub22:workerub22 --chmod=700 container-scripts/worker.bashrc /home/workerub22/.bashrc
ADD --chown=workerub22:workerub22 --chmod=700 container-scripts/worker.test.sh /home/workerub22/.worker-test.sh

############################################

CMD /bin/bash
