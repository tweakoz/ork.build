#!/usr/bin/env python3
###############################################################################
# obt.ix.installdeps.ub26.minimal.py
#
# MINIMAL host prerequisites for RUNNING pip-installed orkid on a fresh
# Ubuntu 26.04 box (not for building the engine — that is
# obt.ix.installdeps.ubuntu_x86_64.py). Exactly the set a stock 26.04
# install was missing (discovered on a fresh Ubuntu 26.04 bring-up, 2026-07-16):
#
#   python3.14-venv  venv module for the host python (pip install target)
#   pkg-config       obt dep scanning at ork.shell launch
#   git              obt env expects it on PATH
#   libjack0         host audio userspace (keep-on-host: never bundled)
###############################################################################

import os

deplist = [
    "python3.14-venv",
    "pkg-config",
    "git",
    "libjack0",
]

os.system("sudo apt update")
os.system("sudo apt -y install %s" % " ".join(deplist))
