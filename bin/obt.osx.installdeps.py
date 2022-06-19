#!/usr/bin/env python3

import os

deplist =  ["cmake","wget","curl","libtiff","libpng"]
deplist += ["portaudio","m4","bison","flex","xz"]
deplist += ["scons","ffmpeg","qt5","zlib"]
deplist += ["mpfr","openssl","graphviz","doxygen","swig","tcl-tk"]

for item in deplist:
    os.system("brew install %s" % item)

os.system("/usr/local/bin/python3 -m pip install --upgrade setuptools")
os.system("/usr/local/bin/pip3 install yarl")
