###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, sys
from pathlib import Path

def wrap(a):
    return Path(str(a))

def root():
  root = Path(os.environ["OBT_ROOT"])
  return root

def zephyr_base():
  return Path(os.environ["ZEPHYR_BASE"])

def deps():
  return root()/"deps"

def patches():
  return root()/"deps"/"patches"

def pysite():
  return root()/"scripts"/"ork"

def python_lib():
  pfx = Path(sys.prefix)
  ver = sys.version_info
  epfx = "python%d.%d" % (ver.major,ver.minor)
  #print(pfx,epfx)
  return pfx/"lib"/epfx

def python_pkg():
  return python_lib()/"site-packages"

def prefix():
  staging = Path(os.environ["OBT_STAGE"])
  return staging

def includes():
  return prefix()/"include"
def libs():
  return prefix()/"lib"

def manifests():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"manifests"

def litex_env_dir():
    return builds()/"litex-buildenv"

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

def vivado_base():
  return Path("/opt/Xilinx/Vivado/2018.3")
