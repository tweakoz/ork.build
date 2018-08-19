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

VER = "2.0.0"
HASH = "2360981cd5d94e1d7a70dfc6983bdf15"

###############################################################################

class avr_libc(dep.Provider):

  def __init__(self,options=None): ############################################

    self.name = "avr-libc-%s" % VER
    self.url = "http://download.savannah.gnu.org/releases/avr-libc/%s.tar.bz2"%self.name
    self.extract_dir = path.builds()/"avr-libc"

    self.arcpath = dep.downloadAndExtract([self.url],
                                           "%s.tar.bz2"%self.name,
                                           "bz2",
                                           HASH,
                                           self.extract_dir)

    self.source_dir = self.extract_dir/self.name
    self.build_dir = self.source_dir/".build"

    os.mkdir(self.build_dir)
    os.chdir(self.build_dir)

    Command(['../configure', 
             '--prefix=%s'%path.prefix(),
             "--build=x86_64-unknown-linux-gnu",
             "--host=avr",
            ]).exec()

    make.exec("all")
    make.exec("install",parallel=False)

    self.OK = True

  def provide(self): ##########################################################
      return self.OK
