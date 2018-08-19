#!/usr/bin/env sh

apt update
apt install autoconf automake bison libbison-dev clang clang-4.0 clang-5.0 cmake curl flex 
apt install make p7zip libsqlite3-dev libusb-dev libzstd-dev unzip g++-6 libgconf-2-4
apt install v4l-utils net-tools ninja-build
apt install libc++abi-dev libc++-dev libssl-dev g++
apt install mesa-common-dev freeglut3-dev 
apt install libxinerama-dev libxcursor-dev libxrandr-dev x11proto-randr-dev
apt install gcc-multilib g++-multilib 
apt install python3 python3-pip git vim wget scons ninja-build 

pip3 install virtualenv
python3 -m pip install python-dateutil
