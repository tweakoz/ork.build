#!/usr/bin/env python3 

from obt import path, pathtools, macos, dep
import os, argparse

parser = argparse.ArgumentParser(description='obt.d build')
parser.add_argument('--alllibs', action="store_true", help='do all libs' )
parser.add_argument('--obt.ibs', action="store_true", help='do obt.d libs' )
parser.add_argument('--obt.ymods', action="store_true", help='do obt.d python modules' )

_args = vars(parser.parse_args())

if _args["alllibs"]!=False:
  for item in pathtools.patglob(path.stage()/"lib","*.dylib"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

if _args["obt.ibs"]!=False:
  for item in pathtools.patglob(path.stage()/"lib","libobt..dylib"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

if _args["obt.ymods"]!=False:
  PYTHON = dep.instance("python")

  for item in pathtools.patglob(PYTHON.site_packages_dir/"obt.ngine"/"core","*.so"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

  for item in pathtools.patglob(PYTHON.site_packages_dir/"obt.ngine"/"lev2","*.so"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

