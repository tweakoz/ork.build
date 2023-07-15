###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, pathtools, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

VERSION = "4.7.0"
###############################################################################

class opencv_contrib(dep.StdProvider):
  name = "opencv_contrib"
  def __init__(self): ############################################
    super().__init__("opencv_contrib")
    self._builder = self.createBuilder(dep.NopBuilder)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=opencv_contrib.name,
                             repospec="opencv/opencv_contrib",
                             revision=VERSION,
                             recursive=False)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"LICENSE").exists()
