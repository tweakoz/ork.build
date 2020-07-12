###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile, sys
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
import ork.command
from ork.command import Command

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import _gcc

deco = Deco()

###############################################################################

class m68k_amiga_gcc(dep.Provider):

  def __init__(self): ############################################
    super().__init__()
    pass

  def provide(self): ##########################################################
    gcc = _gcc.context("m68k-elf")
    toolchain_dir = path.prefix()/"opt"/"toolchain"/"m68k-amiga"
    self.OK = gcc.build(prefix=toolchain_dir)


    self.OK = True

    return self.OK
