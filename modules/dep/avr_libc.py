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

VER = "2.0.0"
HASH = "2360981cd5d94e1d7a70dfc6983bdf15"

###############################################################################

class avr_libc(dep.Provider):

  def __init__(self): ############################################
    super().__init__("avr_libc")

    self.manifest = path.manifests()/"avr_binutils"
    self.OK = self.manifest.exists()
    self.name = "avr-libc-%s" % VER
    self.url = "http://download.savannah.gnu.org/releases/avr-libc/%s.tar.bz2"%self.name
    self.extract_dir = path.builds()/"avr-libc"
    self.source_dir = self.extract_dir/self.name
    self.build_dir = self.source_dir/".build"
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "Avr GCC (source)"

  ########

  def provide(self): ##########################################################
    if False==self.OK:

      self.arcpath = dep.downloadAndExtract([self.url],
                                             "%s.tar.bz2"%self.name,
                                             "bz2",
                                             HASH,
                                             self.extract_dir)


      os.mkdir(self.build_dir)
      os.chdir(self.build_dir)

      Command(['../configure',
               '--prefix=%s'%path.prefix(),
               "--build=x86_64-unknown-linux-gnu",
               "--host=avr",
              ]).exec()

      make.exec("all")
      make.exec("install",parallelism=0.0)
      self.manifest.touch()
      self.OK = True
      return self.OK
