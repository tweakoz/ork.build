#!/usr/bin/env python3
import os, pathlib


this_dir = pathlib.PosixPath(os.path.dirname(os.path.realpath(__file__)))
print(this_dir)
os.chdir(str(this_dir/".."))
print(os.getcwd())
os.system("rm -rf %s" % str(this_dir/"../dist"))
#os.environ["OBT_DEPLOY_TARGET"] = "linux"
#os.system("python3 setup.py bdist_wheel")
os.environ["OBT_DEPLOY_TARGET"] = "macos"
os.system("python3 setup.py bdist_wheel")
os.system("twine check dist/*")
