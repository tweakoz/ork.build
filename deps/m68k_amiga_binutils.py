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

class m68k_amiga_binutils(dep.Provider):

  def __init__(self): ############################################

    super().__init__()

    self.manifest = path.manifests()/"m68k_amiga_binutils"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "68K BinUtils (source)"

  ########

  def provide(self): ##########################################################

    if False==self.OK:
        bu = _binutils.context("binutils-m68k")
        bdest = bu.build_dir/".build"

        os.mkdir(bdest)
        os.chdir(bdest)

        toolchain_dir = path.prefix()/"opt"/"toolchain"/"m68k-amiga"

        Command(['../configure',
                 '--prefix=%s'%toolchain_dir,
                 '--target=m68k-elf',
                 '--program-prefix=m68k-elf-',
                 '--disable-werror',
                 '--disable-nls']).exec()

        make.exec("all")
        make.exec("install",parallelism=0.0)
        self.manifest.touch()

    self.OK = True
    return self.OK
