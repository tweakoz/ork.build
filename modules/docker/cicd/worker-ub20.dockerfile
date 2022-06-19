FROM ubuntu:focal
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

ADD --chown=root:root --chmod=676 ./container-scripts/obt.ix.installdeps.ubuntu19.py /root/installdeps.py
RUN /root/installdeps.py

############################################
# as workerub20 user
############################################

RUN useradd -p workerub20 -G sudo -ms /bin/bash workerub20
RUN passwd -d workerub20
USER workerub20
ENV USER workerub20
WORKDIR /home/workerub20

############################################
# fetch github key
############################################

RUN mkdir -p ~/.ssh
RUN --mount=type=secret,id=ssh_public,uid=1000 --mount=type=secret,id=ssh_private,uid=1000 ssh-agent bash -c 'ssh-add /run/secrets/ssh_private; ssh-keyscan -H github.com >> ~/.ssh/known_hosts'

############################################

ADD --chown=workerub20:workerub20 "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

############################################
# copy worker implementation files
############################################

ADD --chown=workerub20:workerub20 --chmod=700 ci_impl/*.py /home/workerub20/
ADD --chown=workerub20:workerub20 --chmod=700 ci_impl/*.sh /home/workerub20/
ADD --chown=workerub20:workerub20 --chmod=666 ci_impl/*.svg /home/workerub20/

############################################
# final worker setup
############################################

ADD --chown=workerub20:workerub20 worker20.json /home/workerub20/worker.json

ADD --chown=workerub20:workerub20 --chmod=700 container-scripts/start-worker.sh /home/workerub20/
ADD --chown=workerub20:workerub20 --chmod=700 container-scripts/spin.sh /home/workerub20/
ADD --chown=workerub20:workerub20 --chmod=700 container-scripts/worker.bashrc /home/workerub20/.bashrc
ADD --chown=workerub20:workerub20 --chmod=700 container-scripts/worker.test.sh /home/workerub20/.worker-test.sh

############################################

CMD /bin/bash
