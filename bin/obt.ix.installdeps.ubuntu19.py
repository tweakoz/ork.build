#!/usr/bin/env python3

import os

os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist =  ["libboost-dev","gcc-8","gcc-9","g++-8","g++-9",]
deplist += ["libboost-filesystem-dev","libboost-system-dev","libboost-thread-dev"]
deplist += ["libglfw3-dev","libflac++-dev","scons","git"]
deplist += ["rapidjson-dev","graphviz","doxygen","clang","libtiff-dev"]
deplist += ["portaudio19-dev", "pybind11-dev"]
deplist += ["libpng-dev","clang-format","python-dev"]
deplist += ["iverilog","nvidia-cg-dev","nvidia-cuda-dev", "nvidia-cuda-toolkit"]
deplist += ["libxcb-cursor-dev"]
#deplist += ["libxcb-proto-dev"]
deplist += ["libxcb-keysyms1-dev"]
deplist += ["libxcb-xkb-dev","libxkbcommon-x11-dev"]
deplist += ["libgtkmm-3.0-dev"]
deplist += ["libfltk1.3-dev","freeglut3-dev"]
#deplist += ["libxcb-input-dev"]
#deplist += ["libxcb-xf86drio-dev"]
deplist += ["libfontconfig1-dev"]
deplist += ["libfreetype6-dev"]
deplist += ["libx11-dev"]
deplist += ["libxext-dev"]
deplist += ["libxfixes-dev"]
deplist += ["libxi-dev"]
deplist += ["libxrender-dev"]
deplist += ["libxcb1-dev"]
deplist += ["libx11-xcb-dev"]
deplist += ["libxcb-glx0-dev"]
deplist += ["libavformat-dev"]
deplist += ["libavcodec-dev"]
deplist += ["libswscale-dev"]
deplist += ["libssl-dev"]
deplist += ["wget","git","vim","cmake","python3-yarl"]
deplist += ["m4","bison","flex"]
deplist += ["libcurl4-openssl-dev"]
deplist += ["libreadline-dev"]
deplist += ["libxcb-xfixes0-dev"]
deplist += ["libsqlite3-dev"]
deplist += ["libtbb-dev"]
deplist += ["openctm-tools"] # ctmviewer
deplist += ["openscad"] # for trimesh
deplist += ["libclang-dev"]
deplist += ["libgmp-dev","libmpfr-dev","texinfo"]
deplist += ["libdrm-dev","libaudiofile-dev","libsndfile-dev"]

merged = " ".join(deplist)
os.system("sudo apt -y install %s" % merged)
