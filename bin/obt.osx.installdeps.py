#!/usr/bin/env python3

import os

deplist =  ["cmake"]

for item in deplist:
    os.system("brew install %s" % item)
