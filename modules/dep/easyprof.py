###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="v2.1.0"

import os, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt.cmake import context

deco = Deco()

###############################################################################

class easyprof(dep.StdProvider):
  name = "easyprof"
  #############################################
  def __init__(self):
    super().__init__(easyprof.name)
    self.declareDep("cmake")

    mpaths = [
      "/opt/homebrew/Cellar/qt\@5/5.15.13_1/lib/cmake"
    ]

    self._builder = self.createBuilder( dep.CMakeBuilder,
                                        modules_paths=mpaths)

    self._builder.setCmVar("CMAKE_PREFIX_PATH","/opt/homebrew/Cellar/qt@5/5.15.13_1/lib/cmake/Qt5Widgets")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=easyprof.name,
                             repospec="yse/easy_profiler",
                             revision=VERSION,
                             recursive=False)

  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libeasy_profiler.so").exists()
