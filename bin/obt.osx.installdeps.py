#!/usr/bin/env python3

import os

deplist =  ["cmake","wget","curl","libtiff","libpng", "git-lfs"]
deplist += ["portaudio","audiofile","m4","bison","flex","xz"]
deplist += ["scons","zlib","tbb", "glew","boost","flac","libsndfile"]
deplist += ["mpfr","openssl","graphviz","doxygen","swig","tcl-tk"]

depliststr = " ".join(deplist)
os.system("brew install %s" % depliststr)

os.system("/usr/local/bin/python3 -m pip install --upgrade setuptools")
os.system("/usr/local/bin/pip3 install yarl")

#echo "[default]" | sudo tee -a /etc/nsmb.conf
#echo "protocol_vers_map=6" | sudo tee -a /etc/nsmb.conf
#echo "port445=no_netbios" | sudo tee -a /etc/nsmb.conf
#sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.netbiosd.plist
