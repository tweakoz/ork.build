FROM ubuntu:xenial
USER root

############################################
# get base OS up to date
############################################

RUN apt update
RUN apt -yq dist-upgrade
RUN apt -yq autoremove

RUN dpkg --add-architecture i386
RUN apt update
RUN apt install -yq libc6:i386 libstdc++6:i386

RUN apt install -yq wget mkisofs gcc g++ make zlib1g-dev vim
RUN apt install -yq libgmp-dev libmpfr-dev mpc lbzip2 bzip2

############################################
# tzdata first to avoid timezone prompt
############################################

RUN apt install -yq tzdata
RUN apt install -yq libusb-1.0-0-dev libqt4-dev qt4-qmake
RUN apt install -yq usbutils

#######################

#ADD setup.sh /home/root/setup.sh
#ADD fetch.sh /home/root/fetch.sh

WORKDIR /home/root
ENV BASEDIR=/home/root
#ENV PATH="${PATH}:/usr/local/psxsdk/bin"

#RUN /home/root/fetch.sh
#RUN /home/root/setup.sh
COPY FX3_SDK_1_3_1_SRC /opt/fx3sdk/FX3_SDK_1_3_1_SRC
COPY firmware /opt/fx3sdk/firmware
COPY util /opt/fx3sdk/util
RUN gcc /opt/fx3sdk/util/elf2img/elf2img.c -o /usr/local/bin/elf2img -Wall

WORKDIR /opt/fx3sdk/util/cyusb_linux_1.0.4
RUN /opt/fx3sdk/util/cyusb_linux_1.0.4/install.sh
RUN /opt/fx3sdk/util/cyusb_linux_1.0.4/install_lib.sh
RUN cp /opt/fx3sdk/util/cyusb_linux_1.0.4/lib/libcyusb.so* /usr/local/lib/

WORKDIR /opt/fx3sdk/util/cyusb_linux_1.0.4/src
RUN make
RUN cp /opt/fx3sdk/util/cyusb_linux_1.0.4/bin/* /usr/local/bin/

WORKDIR /opt/fx3sdk/FX3_SDK_1_3_1_SRC/sdk/firmware/src
ENV PATH="${PATH}:/opt/fx3sdk/util/arm-2011.03/bin"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/lib"
ENV ARMGCC_INSTALL_PATH="/opt/fx3sdk/util/arm-2011.03"
ENV ARMGCC_VERSION="4.5.2"
RUN make CYCONFIG=fx3_debug

WORKDIR /opt/fx3sdk/util/cyfwstorprog_linux/
RUN make
RUN cp cyfwstorprog /usr/local/bin

RUN useradd -ms /bin/bash fx3dev

RUN mkdir /home/fx3dev/examples

#RUN cp -r /home/root/source/psxsdk-20180115/examples/* /home/fx3dev/examples/
#RUN cp /home/root/source/psxsdk-20180115/Makefile.cfg /home/fx3dev/
RUN chown -R fx3dev.fx3dev /home/fx3dev

USER fx3dev
ENV USER fx3dev
ENV PATH="${PATH}:/opt/fx3sdk/util/arm-2011.03/bin"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/lib"
ENV ARMGCC_INSTALL_PATH="/opt/fx3sdk/util/arm-2011.03"
ENV ARMGCC_VERSION="4.5.2"

WORKDIR /home/fx3dev

