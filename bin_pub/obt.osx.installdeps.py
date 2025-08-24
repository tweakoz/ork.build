#!/usr/bin/env python3

import os

deplist =  ["pkgconfig","cmake","wget","curl","libtiff","libpng", "git-lfs"]
deplist += ["portaudio","m4","bison","flex","xz", "gnupg", "fmt"]
deplist += ["scons","zlib","tbb", "glew","flac","libsndfile"]
deplist += ["mpfr","openssl","graphviz","doxygen","swig","tcl-tk"]
deplist += ["pyqt5","qt5", "gcc@13", "xxhash", "autoconf", "automake" ]
deplist += ["vulkan-loader", "vulkan-extensionlayer", "vulkan-headers"]
deplist += ["vulkan-tools", "vulkan-profiles", "vulkan-validationlayers", "vulkan-utility-libraries"]
deplist += ["pandoc", "doctest","ncurses","curlpp","libtar", "libsodium"]

depliststr = " ".join(deplist)
print(depliststr)
os.system("brew install %s" % depliststr)
#os.system("brew remove boost")

os.system("python3 -m pip install --upgrade setuptools")
