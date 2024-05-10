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
class cppzmq(dep.StdProvider):
  name = "cppzmq"
  def __init__(self):
    super().__init__(cppzmq.name)
    self.declareDep("cmake")
    self.declareDep("zmq")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("CPPZMQ_BUILD_TESTS","OFF")
###############################################################################
  def __str__(self):
    return "cppzmq (github-%s)" % VERSION
###############################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=cppzmq.name,
                             repospec="zeromq/cppzmq",
                             revision=VERSION,
                             recursive=True)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"zmq.hpp").exists()
