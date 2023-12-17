#!/usr/bin/env python3 

from obt import path, pathtools, macos, dep, deco, command
import os, argparse
deco = deco.Deco()

parser = argparse.ArgumentParser(description='obt.d build')
parser.add_argument('--alllibs', action="store_true", help='do all libs' )
parser.add_argument('--orklibs', action="store_true", help='do orkid libs' )
parser.add_argument('--orkpymods', action="store_true", help='do orkid python modules' )
parser.add_argument('--boost', action="store_true", help='do boost libs' )

_args = vars(parser.parse_args())


def do_boost():
  for mach_o_path in pathtools.patglob(path.stage()/"lib","libboost*.dylib"):
    dylib_paths = macos.macho_enumerate_dylibs(mach_o_path)
    for inpitem in dylib_paths:
      if(inpitem.find("libboost")==0):
        print(deco.yellow(inpitem))
        outitem = "@rpath/"+inpitem
        command.run(["install_name_tool","-change",inpitem,outitem,mach_o_path],do_log=True)
      else:
        print(inpitem)  

if _args["alllibs"]!=False:
  for item in pathtools.patglob(path.stage()/"lib","*.dylib"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)
  do_boost()

if _args["orklibs"]!=False:
  for item in macos.enumerateOrkLibs(path.stage()/"lib"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

if _args["orkpymods"]!=False:
  PYTHON = dep.instance("python")

  for item in macos.enumerateOrkPyMods(PYTHON.site_packages_dir/"orkengine"/"core"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

  for item in macos.enumerateOrkPyMods(PYTHON.site_packages_dir/"orkengine"/"lev2"):
    macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
    macos.macho_dump(item)

if _args["boost"]!=False:
  do_boost()

