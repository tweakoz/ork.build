#!/usr/bin/env python3
import os, pathlib

version = "0.0.12"

os.environ["OBT_DEPLOY_VERSION"] = version

src_path = "dist/ork.build.tools-%s-py3-none-any.whl"%version
macos_path = "dist/ork.build.tools-%s-py3-macosx_10_10_x86_64.whl"%version
linux_path = "dist/ork.build.tools-%s-py3-manylinux1_x86_64.whl"%version

this_dir = pathlib.PosixPath(os.path.dirname(os.path.realpath(__file__)))
print(this_dir)
os.chdir(str(this_dir/".."))
print(os.getcwd())
os.system("rm -rf %s" % str(this_dir/"../dist"))

def do_build(dest_path, platname):
  print( "######################################################")
  print( "BUILDING %s" % platname)
  print( "######################################################")
  os.environ["OBT_DEPLOY_TARGET"] = platname
  os.system("python3 setup.py bdist_wheel")
  os.system("mv %s %s" % (src_path, dest_path))

do_build(macos_path, "macos")
do_build(linux_path, "linux")

os.system("twine check dist/*.whl")
