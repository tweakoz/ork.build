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

import _gcc

deco = Deco()

###############################################################################

class avr_gcc(dep.Provider):

  def __init__(self): ############################################
    super().__init__("avr_gcc")
    self.manifest = path.manifests()/"avr_gcc"
    self.OK = self.manifest.exists()
    self._archlist = ["x86_64"]


  ########

  def __str__(self):
    return "Avr GCC (source)"

  ########

  def wipe(self):
    os.system("rm -rf %s"%self.source_root)
    os.system("rm -rf %s"%self.build_dest)

  ########

  def provide(self): ##########################################################
    if True: #False==self.OK:
      binutils = dep.require("avr_binutils")
      gcc = _gcc.context("gcc-avr")
      bdest = gcc.build_dir/".build"
      pfx = path.prefix()
      os.mkdir(bdest)
      os.chdir(bdest)

      cmd = Command(['../configure',
                     '--prefix=%s'%path.prefix(),
                     '--target=avr',
                     '--enable-languages=c,c++',
                     '--disable-nls',
                     '--disable-libssp',
                     '--with-dwarf2'
                     '--with-ld=%s'%(pfx/"bin"/"avr-ld"),
                     '--with-as=%s'%(pfx/"bin"/"avr-as"),
                     '--disable-shared',
                     '--disable-threads',
                     '--disable-libgomp',
                     '--libdir=%s'%(pfx/"lib"/"avr-gcc"/gcc.version),
                    ])

      cmd.exec()
      make.exec()
      make.exec("install",parallelism=0.0)

      self.OK = True
      self.manifest.touch()

      return self.OK
