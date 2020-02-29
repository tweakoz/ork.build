#!/usr/bin/env python3

import os

deplist =  ["cmake","wget","curl","libtiff","libpng"]
deplist += ["boost","portaudio","m4","bison","flex"]
deplist += ["scons","ffmpeg"]

for item in deplist:
    os.system("brew install %s" % item)
