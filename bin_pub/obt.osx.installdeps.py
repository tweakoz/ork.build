#!/usr/bin/env python3

import os

deplist =  ["pkgconfig","cmake","wget","curl","libtiff","libpng", "git-lfs"]
deplist += ["portaudio","fmt","m4","bison","flex","xz"]
deplist += ["scons","zlib","tbb", "glew","flac","libsndfile"]
deplist += ["mpfr","openssl","graphviz","doxygen","swig","tcl-tk"]
deplist += ["pyqt5","qt5", "gcc@13", "xxhash", "autoconf", "automake" ]

depliststr = " ".join(deplist)
os.system("brew install %s" % depliststr)
os.system("brew remove boost")

os.system("python3 -m pip install --upgrade setuptools")
