#!/usr/bin/env python3

import os

#os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist =  ["boost"]
deplist += ["wget"]
deplist += ["texinfo"]
deplist += ["m4","bison","flex"]
deplist += ["xorg-x11"]
deplist += ["xorg-server"]
deplist += ["xorg-proto"]
deplist += ["xcb-proto"]
deplist += ["dev-libs/openssl"]
deplist += ["dev-cpp/tbb"]

merged = " ".join(deplist)
os.system("emerge %s" % merged)
