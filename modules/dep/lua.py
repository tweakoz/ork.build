###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v5.2.1"

import os, tarfile
from ork import dep, host, path, git, pathtools, command, patch, env
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
import ork.host
from ork import log

deco = Deco()

###############################################################################

class lua(dep.Provider):

  def __init__(self): ############################################
    super().__init__("lua")
    #print(options)
    self.header_dest = path.prefix()/"include"/"lua"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "lua (lua.org-source-%s)" % VERSION

  ########

  def env_init(self):
    log.marker("registering Lua SDK")

  ########

  def download_and_extract(self): #############################################

    command.system("rm -rf %s"%self.source_root)

    git.Clone("https://github.com/lua/lua",
              self.source_root,
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

    patch.patch_with_dict(self.source_root/"makefile",patch_items)

  def build(self): ############################################################

    self.download_and_extract()
    os.chdir(str(self.source_root))

    cmd = ["make","-j",host.NumCores]

    if ork.host.IsOsx:
        cmd += ["MACOSX_DEPLOYMENT_TARGET=10.14"]

    self.ok = (0 == Command(cmd).exec())

    return self.install()

  def install(self):
    if self.ok:
      cmd = ["cp",self.source_root/"lua",path.bin()/"lua"]
      self.ok = (0 == Command(cmd).exec())
      if self.ok:
        cmd = ["cp",self.source_root/"liblua.a",path.prefix()/"lib"/"liblua.a"]
        self.ok = (0 == Command(cmd).exec())
        if self.ok:
          pathtools.mkdir(self.header_dest,clean=True)
          cmd = ["cp", self.source_root/"*.h",str(self.header_dest)+"/"]
          self.ok = (0 == command.system(cmd))
    return self.ok 

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"makefile").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"lua").exists()
