###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile, sys
from obt import dep, host, path, git, cmake, make, env
from obt.deco import Deco
from obt.wget import wget
import obt.command
from obt.command import Command
from obt import log

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import _gcc

deco = Deco()

###############################################################################

class arm64_gcc(dep.StdProvider):

  def __init__(self): ############################################
    super().__init__("arm64_gcc")
    self.toolchain_dir = path.prefix()/"opt"/"toolchain"/"aarch64-elf"
    self._archlist = ["x86_64"]
    pass

  def __str__(self):
    return "Arm64-Gcc"

  ########

  def env_init(self):
    if self.toolchain_dir.exists():
      log.marker("registering Arm64-Gcc SDK")
      env.append("PATH",self.toolchain_dir/"bin")

  ########

  def build(self): ##########################################################
    gcc = _gcc.context(self)
    return gcc.build( target="aarch64-elf",
                      variant="newlib",
                      program_prefix="arm64-linux-",
                      install_prefix=self.toolchain_dir )

  ########

  def install(self): ##########################################################
    return True
