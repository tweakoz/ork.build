###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v4.3.5"

import os, tarfile
from obt import dep, host, path

###############################################################################

class zmq(dep.StdProvider):
  name = "zmq"
  def __init__(self): ############################################
    super().__init__(zmq.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    if host.IsDarwin:
      self._builder.setCmVar("WITH_TLS","OFF")
  ########################################################################
  def __str__(self): 
    return "zeromq (github-%s)" % VERSION
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=zmq.name,
                             repospec="zeromq/libzmq",
                             revision=VERSION,
                             recursive=True)
  ########################################################################
  def linkenv(self):
    LIBS = ["zmq"]
    return {
        "LIBS": LIBS,
        "LFLAGS": ["-l%s"%item for item in LIBS]
    }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"zmq.h").exists()
