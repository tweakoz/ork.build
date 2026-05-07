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

  # Walk every orkengine subpackage that may carry C-extensions, not just
  # core+lev2. ecs and ecssim were silently slipping through the fixup —
  # _ecs.so kept @executable_path/.. install_names which work for the
  # ork.python wrapper but fail when the venv python imports orkengine.ecs
  # directly (executable_path resolves to .../pyvenv/bin/, not staging/bin/).
  ork_subpkgs = ["core", "lev2", "ecs", "ecssim"]
  for sub in ork_subpkgs:
    pkgdir = PYTHON.site_packages_dir/"orkengine"/sub
    if not pkgdir.exists():
      continue
    for item in macos.enumerateOrkPyMods(pkgdir):
      macos.macho_replace_loadpaths(item,"@executable_path/../lib","@rpath")
      macos.macho_dump(item)

if _args["boost"]!=False:
  do_boost()

