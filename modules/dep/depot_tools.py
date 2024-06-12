###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v4.7.1"

import os, tarfile
from obt import dep, host, path, cmake, git, make, pathtools
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################
class depot_tools(dep.StdProvider):
  name = "depot_tools"
  def __init__(self):
    super().__init__(depot_tools.name)
    self.declareDep("cmake")
    self.declareDep("zmq")
    self._builder = self.createBuilder(dep.NopBuilder)
###############################################################################
  def __str__(self):
    return "depot_tools (github-%s)" % VERSION
###############################################################################
  @property
  def _binpath(self):
    return path.builds()/"depot_tools"
###############################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(name=depot_tools.name)
    fetcher._git_url = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
    fetcher._revision = "main"
    return fetcher
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"zmq.hpp").exists()
