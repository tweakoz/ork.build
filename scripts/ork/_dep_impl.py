###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile
from pathlib import Path
import importlib.util
import ork.path, ork.host
from ork.command import Command, run
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git, host
#from ork import _dep_node
import ork._dep_enumerate

deco = Deco()

###############################################################################

def switch(linux=None,macos=None):
  if host.IsOsx:
    if macos==None:
      assert(False) # dep not supported on platform
    return macos
  elif host.IsIx:
    if linux==None:
      assert(False) # dep not supported on platform
    return linux
  else:
   return linux


