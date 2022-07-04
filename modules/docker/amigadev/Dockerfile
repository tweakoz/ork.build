ARG UID=1000
ARG GID=1000

FROM sebastianbergmann/amiga-gcc
USER root

RUN apt update -y -qq
RUN apt install -y -qq  python3 
RUN apt install -y -qq  make 
RUN apt install -y -qq  git 
RUN apt install -y -qq  ninja-build 
RUN apt install -y -qq  cmake 
RUN apt install -y -qq  vim 
RUN apt install -y -qq  wget

RUN chmod -R ugo+r /opt/amiga

RUN useradd -p amigadev -ms /bin/bash amigadev
#RUN passwd -d amigadev
USER amigadev
ENV USER amigadev
WORKDIR /home/amigadev

RUN wget http://phoenix.owl.de/tags/vasm1_9.tar.gz
RUN tar xvf vasm1_9.tar.gz
WORKDIR /home/amigadev/vasm
RUN make CPU=m68k SYNTAX=mot 

USER root
RUN cp vasmm68k_mot /usr/bin
RUN cp vobjdump /usr/bin

WORKDIR /home/amigadev
USER amigadev

# Install Build Essentials
#RUN apt-get update && apt-get install build-essential -y && apt-get install file -y && apt-get install apt-utils -y
