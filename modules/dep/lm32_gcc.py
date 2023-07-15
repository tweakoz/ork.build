###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile, sys
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
import obt.command
from obt.command import Command

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import _gcc

deco = Deco()

###############################################################################

class lm32_gcc(dep.Provider):

  def __init__(self): ############################################
    super().__init__("lm32_gcc")
    self._archlist = ["x86_64"]
    pass

  def provide(self): ##########################################################
    gcc = _gcc.context("lm32-elf")
    self.OK = gcc.build()


    self.OK = True

    return self.OK
