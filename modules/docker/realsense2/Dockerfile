FROM python:3.7.4

WORKDIR /home

ENV DEBIAN_FRONTEND=noninteractive 
ENV TZ=Europe/Minsk

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \ 
    sudo \ 
    cmake \
    git \
    curl \
    libopencv-dev \ 
    libjpeg-dev \ 
    libpng-dev \ 
    libtiff-dev \  
    libgtk2.0-dev \ 
    python-numpy \ 
    python-pycurl \ 
    keyboard-configuration \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libusb-1.0-0-dev \
    libglfw3-dev \
    freeglut3 \
    at \
    freeglut3-dev \
    nano \
    curl \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    at \ 
    udev \
    linux-headers-* \
    libusb-1.0-0-dev \
    mesa-utils \
    x11-utils \
    libboost-dev \
    libboost-filesystem-dev libboost-system-dev libboost-thread-dev \
    libboost-program-options-dev libftdi-dev \
    libglfw3-dev libflac++-dev scons git \
    rapidjson-dev graphviz doxygen clang libtiff-dev \
    portaudio19-dev  pybind11-dev \
    libpng-dev clang-format \
    libopenblas-dev \
    librtmidi-dev \
    texinfo xmlto \
    libgtkmm-3.0-dev \
    libfltk1.3-dev freeglut3-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libavformat-dev \
    libavcodec-dev \
    libswscale-dev \
    libssl-dev \
    wget git git-lfs  vim cmake python3-yarl \
    m4 bison flex \
    libcurl4-openssl-dev \
    libreadline-dev \
    libsqlite3-dev \
    libtbb-dev \
    libclang-dev \
    libgmp-dev libmpfr-dev texinfo libmpc-dev \
    libmad0-dev libsdl2-dev libassimp-dev \
    device-tree-compiler \
    imagemagick \
    libdrm-dev libaudiofile-dev libsndfile1-dev 

#update cmake
RUN sudo apt remove cmake -y && \
    wget https://github.com/Kitware/CMake/releases/download/v3.23.0/cmake-3.23.0.tar.gz && \
    tar -xf cmake-3.23.0.tar.gz && \
    cd cmake-3.23.0 && \
    ./configure && \
    make -j$(nproc)  && \
    sudo make install -j$(nproc) 


#install realsense
RUN git clone https://github.com/IntelRealSense/librealsense && \
    cd librealsense && \
    git checkout v2.51.1 && \
    mkdir -p /etc/udev/rules.d && \
    mkdir build && cd build && \
    cmake .. && \
    make install -j$(nproc) && \
    make -j$(nproc) 

RUN useradd -p realsense2 -ms /bin/bash realsense2
WORKDIR /home/realsense2
ENV HOME=/home/realsense2
