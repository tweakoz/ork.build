#!/usr/bin/env python3

import os

deplist =  ["cmake","wget","curl","libtiff","libpng"]
deplist += ["boost","portaudio","m4","bison","flex"]
deplist += ["scons","ffmpeg","qt5","rapidjson","zlib"]
deplist += ["mpfr","openssl"]

for item in deplist:
    os.system("brew install %s" % item)

os.system("pip3 install yarl")
