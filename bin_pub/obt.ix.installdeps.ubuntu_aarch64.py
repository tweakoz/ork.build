#!/usr/bin/env python3

import os, distro

UBUNTU_VERSION = int(float(distro.version())*100.0)

os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist = []

if UBUNTU_VERSION <= 2004:
  deplist +=  ["gcc-8","g++-8","python-dev"] # not avail in ub22

if UBUNTU_VERSION >= 2404:
  deplist += ["clang-18", "g++-11", "g++-10"]
elif UBUNTU_VERSION >= 2304:
  deplist += ["clang-17", "g++-13", "libstdc++-13-dev"]
elif UBUNTU_VERSION >= 2204:
  deplist += ["clang-12", "g++-12", "libstdc++-12-dev"]
else:
  deplist += ["clang-10", "g++-10", "libstdc++-10-dev"]

os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist += ["libboost-dev"]
deplist += ["libboost-filesystem-dev","libboost-system-dev","libboost-thread-dev"]
deplist += ["libboost-program-options-dev"]
deplist += ["libglfw3-dev","libflac++-dev","scons","git"]
deplist += ["rapidjson-dev","graphviz","doxygen","libtiff-dev"]
deplist += ["portaudio19-dev", "pybind11-dev"]
deplist += ["libpng-dev","clang-format"]
deplist += ["libopenblas-dev","libncurses-dev"]
deplist += ["librtmidi-dev","libusb-1.0-0-dev"]
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
deplist += ["libssl-dev", "libbz2-dev"]
deplist += ["wget","git","git-lfs", "vim","cmake", "python3-pip"]
deplist += ["m4","bison","flex"]
deplist += ["libcurl4-openssl-dev"]
deplist += ["libreadline-dev"]
deplist += ["libsqlite3-dev"]
deplist += ["libtbb-dev"]
deplist += ["libglew-dev"] # ctmviewer
deplist += ["mesa-utils"] 
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
deplist += ["imagemagick"]

deplist += ["libdrm-dev","libaudiofile-dev","libsndfile1-dev"]

deplist += ["gfortran"]
deplist += ["ocl-icd-opencl-dev"]
deplist += ["libfmt-dev"]
deplist += ["meson","ninja-build","libserialport-dev", "libxxhash-dev"]
deplist += ["libpipewire-0.3-dev", "pipewire"]

merged = " ".join(deplist)
os.system("sudo apt -y install %s" % merged)
