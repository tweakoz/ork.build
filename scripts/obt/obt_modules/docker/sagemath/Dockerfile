# source https://www.nantenaina.xyz/posts/Sagemath-Development-Environment/

FROM ubuntu:focal
USER root

RUN apt -yq clean
RUN apt -yq update
RUN apt -yq dist-upgrade
RUN apt -yq autoremove

RUN DEBIAN_FRONTEND=noninteractive TZ=Americas/US apt install -yq bc binutils bzip2 ca-certificates cliquer curl \
                    eclib-tools fflas-ffpack flintqs g++ g++ gcc gcc gfan gfortran \
                    git glpk-utils gmp-ecm lcalc libatomic-ops-dev libboost-dev \
                    libbraiding-dev libbrial-dev libbrial-groebner-dev libbz2-dev \
                    libcdd-dev libcdd-tools libcliquer-dev libcurl4-openssl-dev \
                    libec-dev libecm-dev libffi-dev libflint-arb-dev libflint-dev \
                    libfreetype6-dev libgc-dev libgd-dev libgf2x-dev libgiac-dev \
                    libgivaro-dev libglpk-dev libgmp-dev libgsl-dev libiml-dev \
                    liblfunction-dev liblrcalc-dev liblzma-dev libm4rie-dev libmpc-dev \
                    libmpfi-dev libmpfr-dev libncurses5-dev libntl-dev libopenblas-dev \
                    libpari-dev libpcre3-dev libplanarity-dev libppl-dev libpython3-dev \
                    libreadline-dev librw-dev libsqlite3-dev libsuitesparse-dev \
                    libsymmetrica2-dev libz-dev libzmq3-dev libzn-poly-dev m4 make \
                    nauty palp pari-doc pari-elldata pari-galdata pari-galpol pari-gp2c \
                    pari-seadata patch perl pkg-config planarity ppl-dev python3 \
                    python3-dev python3-distutils r-base-dev r-cran-lattice sqlite3 \
                    sympow tachyon tar xcas xz-utils yasm \
                    dvipng texlive ffmpeg default-jdk pandoc libavdevice-dev \
    && apt autoremove \
    && apt autoclean \
    && rm -r /var/lib/apt/lists/*


ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash

ARG SAGE_ROOT=/home/sage/sage
RUN ln -s "$SAGE_ROOT/sage" /usr/bin/sage

ARG HOME=/home/sage
RUN mkdir -p /etc/sudoers.d
RUN adduser --quiet --shell /bin/bash --gecos "Sage user,101,," --disabled-password --home "$HOME" sage \
    && echo "sage ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/01-sage \
    && chmod 0440 /etc/sudoers.d/01-sage


USER sage
WORKDIR ${HOME}

COPY downloads/sage-9.6.tar.gz sage-9.6.tar.gz
RUN tar -xvf sage-9.6.tar.gz
RUN mv sage-9.6 sage
RUN cd sage && ./configure && make -j4
RUN rm -rf /home/sage/sage-9.6.tar.gz

RUN sage -pip install terminado "notebook>=5" "ipykernel>=4.6"
RUN sage -i gap_jupyter singular_jupyter pari_jupyter

#ENV LD_PRELOAD /usr/lib/aarch64-linux-gnu/libgomp.so.1
ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libgomp.so.1

CMD [ "bash" ]