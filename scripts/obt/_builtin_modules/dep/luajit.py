###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v2.1"

import os, tarfile
from yarl import URL
from obt import dep, host, path, git, pathtools, patch
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
import obt.host
import fileinput

deco = Deco()

###############################################################################

class luajit(dep.StdProvider):
  name = "luajit"
  def __init__(self): ############################################
    super().__init__(luajit.name)
    self._builder = dep.CustomBuilder(luajit.name)
    bdir = self.source_root

    cmdlist = ["make","-j",host.NumCores]

    if obt.host.IsOsx:
        cmdlist += ["MACOSX_DEPLOYMENT_TARGET=10.15"]

    clean_cmd = Command(cmdlist+["clean"],working_dir=bdir)
    install_cmd = Command(cmdlist+["install"],working_dir=bdir)

    self._builder._cleanbuildcommands += [clean_cmd,install_cmd]
    self._builder._incrbuildcommands = [install_cmd]
    self._builder._builddir = bdir

  ########

  def __str__(self):
    return "LuaJit (luajit.org-source-%s)" % VERSION

  ########################################################################
  @property
  def _fetcher(self):
    makefile_items = dict()
    makefile_items["export PREFIX= /usr/local"]="export PREFIX=%s"%path.prefix()
    patch_dict = { self.source_root/"Makefile": makefile_items }
    return dep.GithubFetcher(name=luajit.name,
                             repospec="LuaJIT/LuaJIT",
                             revision=VERSION,
                             recursive=False,
                             patchdict=patch_dict)

  ########

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"luajit-2.1").exists()
