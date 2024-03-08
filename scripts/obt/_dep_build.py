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
import obt.path, obt.host
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, make, path, git, host, _globals, log
from obt._dep_impl import require
from collections.abc import Callable

deco = Deco()

###############################################################################
# BaseBuilder : builder basic interface
###############################################################################

class BaseBuilder(object):
  def __init__(self,name):
    super().__init__()
    self._name = name
    self._deps = []
    self._debug = False
    self._onPostBuild = None
    self._onPostInstall = None
  def requires(self,deplist):
    """declare that this dep module depends on others"""
    self._deps += deplist
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    """execute build phase"""
    require(self._deps)
  def install(self,blddir):
    """execute install phase"""
    return True

###############################################################################
# NopBuilder : do nothing builder (but still installs child dependencies)
###############################################################################

class NopBuilder(BaseBuilder):
  """Do nothing builder (but still installs child dependencies)"""
  def __init__(self,name):
    super().__init__(name)
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    return True
