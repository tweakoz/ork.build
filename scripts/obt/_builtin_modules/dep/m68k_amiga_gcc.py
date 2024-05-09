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

class m68k_amiga_gcc(dep.StdProvider):

  def __init__(self): ############################################
    super().__init__("m68k_amiga_gcc")
    self.toolchain_dir = path.prefix()/"opt"/"toolchain"/"m68k-amiga"
    self._archlist = ["x86_64"]
    pass

  def __str__(self):
    return "Amiga-68k-Gcc"

  ########

  def env_init(self):
    if (self.toolchain_dir/"bin").exists():
      log.marker("registering AmigaGCC SDK")
      env.append("PATH",self.toolchain_dir/"bin")

  ########

  def build(self): ##########################################################
    gcc = _gcc.context(self)
    return gcc.build( target="m68k-elf",
                      program_prefix="m68k-elf-amiga-",
                      install_prefix=self.toolchain_dir )==0

  ########

  def install(self): ##########################################################
    return True
