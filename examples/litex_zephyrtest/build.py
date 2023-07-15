#!/usr/bin/env python3

from obt import path, pathtools, utils
import os

build_dir = path.builds()/"litex_zephyrtest"
src_dir = os.path.dirname(os.path.realpath(__file__))

pathtools.mkdir(build_dir,clean=True)
pathtools.chdir(build_dir)
os.system("cmake %s"%str(this_dir))
os.system("make -j %d"%utils.num_cores)
