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
from obt.command import Command

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import _binutils

deco = Deco()

###############################################################################

class avr_binutils(dep.Provider):

  def __init__(self): ############################################

    super().__init__("avr_binutils")

    self.manifest = path.manifests()/"avr_binutils"
    self.OK = self.manifest.exists()
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "Avr BinUtils (source)"

  ########

  def provide(self): ##########################################################

    if False==self.OK:
        bu = _binutils.context("binutils-avr")
        bdest = bu.build_dir/".build"

        os.mkdir(bdest)
        os.chdir(bdest)

        Command(['../configure',
                 '--prefix=%s'%path.prefix(),
                 '--target=avr',
                 '--disable-werror',
                 '--disable-nls']).exec()

        make.exec("all")
        make.exec("install",parallelism=0.0)
        self.manifest.touch()

    self.OK = True
    return self.OK
