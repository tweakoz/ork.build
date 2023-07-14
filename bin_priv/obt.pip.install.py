#!/usr/bin/env python3

import os, sys
import ork.pip

if not len(sys.argv) == 2:
  print("usage: package to install")
  sys.exit(1)

ork.pip.install(sys.argv[1])
