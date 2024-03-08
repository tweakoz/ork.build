from obt._dep_build import BaseBuilder
from obt._dep_impl import require
from obt import pathtools, path, _globals
from obt.command import Command
import obt.host
from collections.abc import Callable

###############################################################################
# BinInstaller : install binaries from downloaded package
###############################################################################

class BinInstaller(BaseBuilder):
  """Install binaries from downloaded package"""
  ###########################
  class InstallerItem:
    def __init__(self,src,dst,flags):
      self._src = src
      self._dst = dst
      self._flags = flags
  ###########################
  def __init__(self,name):
    super().__init__(name)
    self._items = []
    self._OK = True
  ###########################################
  """declare an install item given a source-path and dest-path"""
  def install_item(self,
                   source=None,
                   destination=None,
                   flags=None):
    self._items += [BinInstaller.InstallerItem(source,destination,flags)]
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    ok2build = require(self._deps)
    if not ok2build:
      return False
    for item in self._items:
      exists = item._src.exists()
      #print(item,item._src,exists)
      if False==exists:
        self._OK = False
        return False
    return True
  ###########################################
  def install(self,blddir):
    for item in self._items:
      cmd = [
        "cp", item._src, item._dst
      ]
      Command(cmd).exec()
      if item._flags != None:
        cmd = [
          "chmod",item._flags, item._dst
        ]
        Command(cmd).exec()
    return self._OK

