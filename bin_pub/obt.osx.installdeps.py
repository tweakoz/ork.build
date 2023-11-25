#!/usr/bin/env python3

import os

deplist =  ["cmake","wget","curl","libtiff","libpng", "git-lfs"]
deplist += ["portaudio","audiofile","m4","bison","flex","xz"]
deplist += ["scons","zlib","tbb", "glew","boost","flac","libsndfile"]
deplist += ["mpfr","openssl","graphviz","doxygen","swig","tcl-tk"]
deplist += ["pyqt5","qt5"]

depliststr = " ".join(deplist)
os.system("brew install %s" % depliststr)

os.system("/usr/local/bin/python3 -m pip install --upgrade setuptools")
