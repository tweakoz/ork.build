###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class simavr(dep.Provider):

  def __init__(self): ############################################
    super().__init__("simavr")
    self.source_root = path.builds()/"simavr"
    self._archlist = ["x86_64"]

  def provide(self): ##########################################################

    git.Clone("https://github.com/tweakoz/simavr",self.source_root,"master")
    # INSTALL_PREFIX consumed by simavr's Makefile via env. Per-Command env
    # would be cleaner, but make.exec doesn't take an env kwarg today and
    # this is a low-priority dep; leave the env.set as-is.
    os.environ["INSTALL_PREFIX"] = str(path.prefix())
    OK = make.exec("install", working_dir=self.source_root)
    if OK:
      self.manifest.touch()
    return OK
