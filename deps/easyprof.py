###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="v2.1.0"

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class easyprof(dep.StdProvider):
  #############################################
  def __init__(self):
    name = "easyprof"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="yse/easy_profiler",
                                      revision=VERSION,
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
  #############################################
