###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v5.2.1"

import os, tarfile
from ork import dep, host, path, git, pathtools, command, patch
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
import ork.host

deco = Deco()

###############################################################################

class lua(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(lua,self)
    parclass.__init__(miscoptions=miscoptions)
    #print(options)
    self.source_dest = path.builds()/"lua"
    self.build_dest = self.source_dest
    self.header_dest = path.prefix()/"include"/"lua"
    self.manifest = path.manifests()/"lua"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "lua (lua.org-source-%s)" % VERSION

  ########

  def download_and_extract(self): #############################################

    command.system("rm -rf %s"%self.source_dest)

    git.Clone("https://github.com/lua/lua",
              self.source_dest,
              rev=VERSION,
              cache=False)

    patch_items = dict()
    patch_items["CC= clang-3.8"]="CC= g++"
    patch_items["CFLAGS= -Wall -O2 $(MYCFLAGS)"]="CFLAGS= -Wall -O2 $(MYCFLAGS) -fPIC"
    if ork.host.IsLinux:
        patch_items["MYLDFLAGS= $(LOCAL) -Wl,-E"]="MYLDFLAGS= $(LOCAL) -Wl,-E -fPIC"
    else:
        patch_items["MYLDFLAGS= $(LOCAL) -Wl,-E"]="MYLDFLAGS= $(LOCAL) -fPIC"
        patch_items["-lhistory"]=""

    patch.patch_with_dict(self.source_dest/"makefile",patch_items)

  def build(self): ############################################################

    self.download_and_extract()
    os.chdir(str(self.source_dest))

    cmd = ["make","-j",host.NumCores]

    if ork.host.IsOsx:
        cmd += ["MACOSX_DEPLOYMENT_TARGET=10.14"]

    ok = (0 == Command(cmd).exec())
    if ok:
      cmd = ["cp",self.source_dest/"liblua.a",path.prefix()/"lib"/"liblua.a"]
      ok = (0 == Command(cmd).exec())
      if ok:
        pathtools.mkdir(self.header_dest,clean=True)
        cmd = ["cp", self.source_dest/"*.h",str(self.header_dest)+"/"]
        ok = (0 == command.system(cmd))

    return ok
