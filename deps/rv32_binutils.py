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
from ork.command import Command

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import _binutils

deco = Deco()

###############################################################################

class rv32_binutils(dep.Provider):

  def __init__(self,options=None): ############################################
    pass


  def provide(self): ##########################################################
    bu = _binutils.context("binutils-rv32")
    bdest = bu.build_dir/".build"

    os.mkdir(bdest)
    os.chdir(bdest)

    Command(['../configure',
             '--prefix=%s'%path.prefix(),
             '--program-prefix=riscv32-elf-',
             '--target=riscv32-elf']).exec()

    make.exec("all")
    make.exec("install",parallel=False)

    self.OK = True
    return self.OK