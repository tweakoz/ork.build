#!/usr/bin/env python3

import os, sys
import obt.pip

if not len(sys.argv) == 2:
  print("usage: package to install")
  sys.exit(1)

obt.pip.install(sys.argv[1])
