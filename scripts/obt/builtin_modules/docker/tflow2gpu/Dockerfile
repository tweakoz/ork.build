FROM tensorflow/tensorflow:2.9.1-gpu

ARG UID=1000
ARG GID=1000
WORKDIR /root

############################################
# tzdata first to avoid timezone prompt
############################################

RUN apt update

RUN curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg
RUN mv bazel.gpg /etc/apt/trusted.gpg.d/
RUN echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list

RUN apt update
RUN apt install -yq tzdata

############################################

# Dependencies for glvnd and X11.
RUN apt-get install -y -qq libglvnd0
RUN apt-get install -y -qq libgl1
RUN apt-get install -y -qq libglx0
RUN apt-get install -y -qq libegl1
RUN apt-get install -y -qq libxext6
RUN apt-get install -y -qq libx11-6
RUN apt-get install -y -qq glmark2
RUN apt-get install -y -qq mesa-utils
RUN apt-get install -y -qq freeglut3-dev
RUN apt-get install -y -qq apt-transport-https curl gnupg
RUN apt-get install -y -qq bazel
RUN apt-get install -y -qq git cmake gdb
RUN apt-get install -y -qq build-essential
RUN apt-get install -y -qq gcc-8 g++-8
RUN apt-get install -y -qq ca-certificates
RUN apt-get install -y -qq ffmpeg
RUN apt-get install -y -qq git
RUN apt-get install -y -qq wget
RUN apt-get install -y -qq unzip
RUN apt-get install -y -qq python3-dev
RUN apt-get install -y -qq python3-opencv
RUN apt-get install -y -qq python3-pip
RUN apt-get install -y -qq libopencv-core-dev
RUN apt-get install -y -qq libopencv-highgui-dev
RUN apt-get install -y -qq libopencv-imgproc-dev
RUN apt-get install -y -qq libopencv-video-dev
RUN apt-get install -y -qq libopencv-calib3d-dev
RUN apt-get install -y -qq libopencv-features2d-dev
RUN apt-get install -y -qq software-properties-common
RUN add-apt-repository -y ppa:openjdk-r/ppa
RUN apt-get update 
RUN apt-get install -y openjdk-8-jdk
RUN apt-get install -y mesa-common-dev libegl1-mesa-dev libgles2-mesa-dev
RUN apt-get install -y mesa-utils
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 100 --slave /usr/bin/g++ g++ /usr/bin/g++-8
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Env vars for the nvidia-container-runtime.

RUN useradd -ms /bin/bash tensorflow

USER tensorflow
ENV USER tensorflow
WORKDIR /home/tensorflow

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES graphics,utility,compute
# Add gym.
RUN /usr/bin/python3 -m pip install --upgrade pip
RUN pip install --upgrade pip \
  && pip install gym==0.17.2 box2d==2.3.10

RUN pip3 install --upgrade setuptools
RUN pip3 install wheel
RUN pip3 install future
RUN pip3 install six==1.14.0
RUN pip3 install tensorflow==2.2.0
RUN pip3 install tf_slim

RUN git clone https://github.com/google/mediapipe.git
