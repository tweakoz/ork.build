###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v1.10.0"

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

class lz4(dep.StdProvider):
  name = "lz4"
  def __init__(self): ############################################
    super().__init__(lz4.name)
    self._builder = dep.CustomBuilder(lz4.name)
    bdir = self.source_root

    cmdlist = ["make","-j",host.NumCores,"PREFIX=%s"%path.prefix()]

    if obt.host.IsOsx:
        cmdlist += ["MACOSX_DEPLOYMENT_TARGET=10.15"]

    clean_cmd = Command(cmdlist+["clean"],working_dir=bdir)
    install_cmd = Command(cmdlist+["install"],working_dir=bdir)

    self._builder._cleanbuildcommands += [clean_cmd,install_cmd]
    self._builder._incrbuildcommands = [install_cmd]
    self._builder._builddir = bdir

  ########

  def __str__(self):
    return "lz4 (lz4.org-source-%s)" % VERSION

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=lz4.name,
                             repospec="lz4/lz4",
                             revision=VERSION,
                             md5val="828d4914ca1ce5ce59a52d684ca88e44", # v1.10.0
                             recursive=False)

  ########

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"lz4-1.10.0").exists()
