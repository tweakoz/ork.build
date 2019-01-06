###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, sys
from pathlib import Path

def deps():
  root = Path(os.environ["OBT_ROOT"])
  return root/"deps"

def patches():
  root = Path(os.environ["OBT_ROOT"])
  return root/"deps"/"patches"

def pysite():
  root = Path(os.environ["OBT_ROOT"])
  return root/"scripts"/"ork"

def python_lib():
  pfx = Path(sys.prefix)
  ver = sys.version_info
  epfx = "python%d.%d" % (ver.major,ver.minor)
  print(pfx,epfx)
  return pfx/"lib"/epfx

def python_pkg():
  return python_lib()/"site-packages"

def prefix():
  staging = Path(os.environ["OBT_STAGE"])
  return staging

def manifests():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"manifests"

def downloads():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"downloads"

def gitcache():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"gitcache"

def builds():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"builds"

def project_root():
  root = Path(os.environ["ORK_PROJECT_ROOT"])
  return root
