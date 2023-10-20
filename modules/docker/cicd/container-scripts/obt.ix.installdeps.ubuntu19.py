#!/usr/bin/env python3

import os

os.system("pip3 install os_release distro")
os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist =  ["libboost-dev","gcc-8","gcc-9","g++-8","g++-9","gcc-10","g++-10"]
deplist += ["libboost-filesystem-dev","libboost-system-dev","libboost-thread-dev"]
deplist += ["libboost-program-options-dev","libftdi-dev"]
deplist += ["libglfw3-dev","libflac++-dev","scons","git"]
deplist += ["rapidjson-dev","graphviz","doxygen","clang","libtiff-dev"]
deplist += ["portaudio19-dev", "pybind11-dev"]
deplist += ["libpng-dev","clang-format","python-dev"]
deplist += ["iverilog","nvidia-cg-dev","nvidia-cuda-dev", "nvidia-cuda-toolkit"]
deplist += ["libopenblas-dev"]
deplist += ["librtmidi-dev"]
deplist += ["texinfo"]
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
deplist += ["wget","git","git-lfs", "vim","cmake","python3-yarl"]
deplist += ["m4","bison","flex"]
deplist += ["libcurl4-openssl-dev"]
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
deplist += ["imagemagick"]

deplist += ["libdrm-dev","libaudiofile-dev","libsndfile1-dev"]

merged = " ".join(deplist)
os.system("sudo apt -y install %s" % merged)

