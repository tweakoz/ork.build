#!/usr/bin/env python3

import os, distro

UBUNTU_VERSION = int(float(distro.version())*100.0)

print(UBUNTU_VERSION)
os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist = []

if UBUNTU_VERSION >= 2310:
  deplist =  ["clang-17"]
elif UBUNTU_VERSION <= 2004:
  deplist =  ["gcc-8","g++-8","python-dev"] # not avail in ub22
else:
  deplist += ["clang-12"]

deplist += ["libboost-dev","gcc-9","g++-9","gcc-10","g++-10","clang","clang-format"]
deplist += ["g++-12","gfortran"] # https://askubuntu.com/questions/1441844/todays-ubuntu-22-04-updates-seem-to-break-clang-compiler
deplist += ["libboost-filesystem-dev","libboost-system-dev","libboost-thread-dev"]
deplist += ["libboost-program-options-dev","libftdi-dev", "libfmt-dev"]
deplist += ["libglfw3-dev","libflac++-dev","scons","git"]
deplist += ["rapidjson-dev","graphviz","doxygen","libtiff-dev"]
deplist += ["portaudio19-dev", "pybind11-dev"]
deplist += ["libpng-dev"]
deplist += ["iverilog","nvidia-cg-dev","nvidia-cuda-dev", "nvidia-cuda-toolkit"]
deplist += ["libopenblas-dev"]
deplist += ["librtmidi-dev"]
deplist += ["texinfo","xmlto"]
deplist += ["libgtkmm-3.0-dev"]
deplist += ["libfltk1.3-dev","freeglut3-dev"]
deplist += ["libfontconfig1-dev"]
deplist += ["libfreetype6-dev"]
deplist += ["libx11-dev"]
deplist += ["libxext-dev"]
deplist += ["libxfixes-dev"]
deplist += ["libxi-dev"]
deplist += ["libxrender-dev"]
deplist += ["libx11-xcb-dev"]
deplist += ["libavformat-dev"]
deplist += ["libavcodec-dev"]
deplist += ["libswscale-dev"]
deplist += ["libssl-dev"]
deplist += ["wget","git","git-lfs", "vim","cmake","python3-pip", "nasm"]
deplist += ["m4","bison","flex"]
deplist += ["libcurl4-openssl-dev","libusb-1.0-0-dev", "libbz2-dev"]
deplist += ["libreadline-dev"]
deplist += ["libsqlite3-dev"]
deplist += ["libtbb-dev"]
deplist += ["openctm-tools"] # ctmviewer
deplist += ["openscad"] # for trimesh
deplist += ["libclang-dev"]
deplist += ["libgmp-dev","libmpfr-dev","texinfo","libmpc-dev"]
deplist += ["libx11-dev"]
deplist += ["libx11-xcb-dev"]
deplist += ["libxext-dev"]
deplist += ["libxfixes-dev"]
deplist += ["libxi-dev"]
deplist += ["libxrender-dev"]
deplist += ["libxcb1-dev"]
deplist += ["libxcb-glx0-dev"]
deplist += ["libxcb-keysyms1-dev"]
deplist += ["libxcb-image0-dev"]
deplist += ["libxcb-shm0-dev"]
deplist += ["libxcb-icccm4-dev"]
deplist += ["libxcb-sync-dev"]
deplist += ["libxcb-xfixes0-dev"]
deplist += ["libxcb-shape0-dev"]
deplist += ["libxcb-randr0-dev"]
deplist += ["libxcb-render-util0-dev"]
deplist += ["libxcb-xinerama0-dev"]
deplist += ["libxkbcommon-dev"]
deplist += ["libxkbcommon-x11-dev"]
deplist += ["libxcb-xkb-dev"]
deplist += ["libxcb-cursor-dev"]
deplist += ["libxcb-util-dev"]
deplist += ["libmad0-dev","libsdl2-dev","libassimp-dev"]
deplist += ["device-tree-compiler"]
deplist += ["imagemagick","curl","tk-dev"]
deplist += ["libgeos-dev","libpng-dev","libspatialindex-dev"]
deplist += ["qt5-style-plugins","qt5ct","python3-gdal","python3-pyqt5","python3-pyqt5.qtopengl"]
deplist += ["python3-simplejson","python3-tk"]

deplist += ["libdrm-dev","libaudiofile-dev","libsndfile1-dev"]
deplist += ["libglew-dev"]
deplist += ["debhelper-compat","findutils","git","libasound2-dev","libavcodec-dev","libavfilter-dev","libavformat-dev"]
deplist += ["libdbus-1-dev","libbluetooth-dev","libglib2.0-dev","libgstreamer1.0-dev","libgstreamer-plugins-base1.0-dev"]
deplist += ["libsbc-dev","libsdl2-dev","libudev-dev","libva-dev","libv4l-dev","libx11-dev","meson","ninja-build"]
deplist += ["pkg-config","python3-docutils","systemd"]


merged = " ".join(deplist)
os.system("sudo apt -y install %s" % merged)

os.system("pip3 install os_release")
