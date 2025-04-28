#!/Users/michael/.venv-apr22/bin/python3

import os

deplist =  ["pkgconfig","cmake","wget","curl","libtiff","libpng", "git-lfs"]
deplist += ["portaudio","m4","bison","flex","xz", "gnupg", "fmt"]
deplist += ["scons","zlib","tbb", "glew","flac","libsndfile"]
deplist += ["mpfr","openssl","graphviz","doxygen","swig","tcl-tk"]
deplist += ["pyqt5","qt5", "gcc@13", "xxhash", "autoconf", "automake" ]

depliststr = " ".join(deplist)
print(depliststr)
os.system("brew install %s" % depliststr)
#os.system("brew remove boost")

os.system("python3 -m pip install --upgrade setuptools")
