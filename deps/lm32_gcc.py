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

import _gcc

deco = Deco()

###############################################################################

class lm32_gcc(dep.Provider):

  def __init__(self,options=None): ############################################
    pass

  def provide(self): ##########################################################
    gcc = _gcc.context("gcc-lm32")

    Command(["rm","-rf",gcc.build_dir/"libstdc++-v3"]).exec()

    bdest = gcc.build_dir/".build"

    os.mkdir(bdest)
    os.chdir(bdest)

    cmd = Command(['../configure', 
                   '--prefix=%s'%path.prefix(),
                   '--target=lm32-elf',
                   '--enable-languages=c,c++',
                   '--disable-libgcc',
                   '--disable-libssp',
                   ])
    cmd.exec()
    make.exec("all")
    make.exec("install",parallel=False)

    self.OK = True

    return self.OK
