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
RUN apt install -yq imagemagick cmake libreadline-dev
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

############################################

RUN pip3 install yarl
RUN pip3 install gitpython
RUN pip3 install pycairo
RUN pip3 install transitions
RUN pip3 install jsonpickle
RUN pip3 install hashfs
RUN pip3 install zmq
RUN pip3 install sshtunnel
RUN pip3 install jinja2
RUN pip3 install ork.build

############################################

#ADD --chown=root:root ./container-scripts/obt.ix.installdeps.ubuntu19.py /root/installdeps.py
#RUN /root/installdeps.py

RUN useradd -ms /bin/bash cimaster

USER cimaster
ENV USER cimaster
RUN mkdir -p ~/.ssh

RUN --mount=type=secret,id=ssh_public,uid=1000 --mount=type=secret,id=ssh_private,uid=1000 ssh-agent bash -c 'ssh-add /run/secrets/ssh_private; ssh-keyscan -H github.com >> ~/.ssh/known_hosts'
WORKDIR /home/cimaster

############################################

ADD --chown=cimaster:cimaster "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

ADD --chown=cimaster:cimaster master.json /home/cimaster/
ADD --chown=cimaster:cimaster container-scripts/start-master.sh /home/cimaster/
RUN chmod u+x /home/cimaster/start-master.sh

RUN mkdir /home/cimaster/assets
ADD --chown=cimaster:cimaster ci_impl/*.py /home/cimaster/
ADD --chown=cimaster:cimaster ci_impl/*.sh /home/cimaster/
ADD --chown=cimaster:cimaster ci_impl/*.svg /home/cimaster/
ADD --chown=cimaster:cimaster ci_impl/assets /home/cimaster/assets/

CMD /bin/bash

