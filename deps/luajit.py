###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from yarl import URL
from ork import dep, host, path, git, pathtools, patch
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
import ork.host
import fileinput

deco = Deco()

###############################################################################

class luajit(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(luajit,self)
    parclass.__init__(miscoptions=miscoptions)
    #print(options)
    self.source_root = path.builds()/"luajit"
    self.build_dest = self.source_root
    self.manifest = path.manifests()/"luajit"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "LuaJit (luajit.org-source-%s)" % VERSION

  ########

  def download_and_extract(self): #############################################

    os.system("rm -rf %s"%self.source_root)

    git.Clone("https://github.com/LuaJIT/LuaJIT",
              self.source_root,
              rev=VERSION)

    #pathtools.mkdir(self.build_dest,clean=True)
    #pathtools.chdir(self.build_dest)

    patch_items = dict()
    patch_items["export PREFIX= /usr/local"]="export PREFIX=%s"%path.prefix()
    patch.patch_with_dict(self.source_root/"Makefile",patch_items)

  def build(self): ############################################################

    self.download_and_extract()
    os.chdir(str(self.source_root))

    cmd = ["make","-j",host.NumCores]

    if ork.host.IsOsx:
        cmd += ["MACOSX_DEPLOYMENT_TARGET=10.14"]

    cmd += ["install"]
    return 0 == Command(cmd).exec()
