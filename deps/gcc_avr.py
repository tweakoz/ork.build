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

import __gcc

deco = Deco()

###############################################################################

class gcc_avr(dep.Provider):

  def __init__(self,options=None): ############################################

    gcc = __gcc.context("gcc-avr")
    bdest = gcc.build_dir/".build"

    os.mkdir(bdest)
    os.chdir(bdest)

    cmd = Command(['../configure', 
                   '--prefix=%s'%path.prefix(),
                   '--target=avr',
                   '--enable-languages=c,c++',
                   '--disable-nls',
                   '--disable-libssp',
                   '--with-dwarf2'
                  ])

    cmd.exec()
    make.exec()
    make.exec("install",parallel=False)

    self.OK = True

  def provide(self): ##########################################################
      return self.OK
