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

class irix65_binutils(dep.StdProvider):

    def __init__(self): ############################################
        super().__init__("mips_irix65_binutils")
        self._archlist = ["x86_64"]

    ########

    def __str__(self):
        return "MIPS/IRIX65 BinUtils (source)"

    ########

    def build(self): ##########################################################

        bu = _binutils.context(self)

        os.mkdir(self.build_dest)
        os.chdir(self.build_dest)

        toolchain_dir = path.prefix()/"opt"/"toolchain"/"mips-sgi-irix6.5"

        ok = Command(['../%s/configure'%bu.name,
                      '--prefix=%s'%toolchain_dir,
                      '--target=mips-sgi-irix6.5',
                      '--program-prefix=mips-sgi-irix6.5-',
                      '--disable-werror',
                      '--disable-nls']).exec()==0

        return make.exec("all")==0

    def install(self): ##########################################################
        os.chdir(self.build_dest)
        return make.exec("install",parallelism=0.0)==0
