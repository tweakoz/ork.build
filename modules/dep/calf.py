###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, pathtools, git, cmake, make, command
from obt.deco import Deco
from obt.wget import wget

deco = Deco()

VERSION = "master"
###############################################################################

class calf(dep.Provider):

  def __init__(self): ############################################
    super().__init__("calf")
    self.source_root = path.builds()/"calf"
    self.build_dest = self.source_root/".build"

  ########

  def __str__(self):
    return "CALF (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    dep.require("fluidsynth")
    self.OK = False


    os.system("rm -rf %s"%self.source_root)

    git.Clone("https://github.com/calf-studio-gear/calf",
              self.source_root,
              VERSION)

    pathtools.chdir(self.source_root)

    os.system("aclocal --force")
    os.system("libtoolize --force --automake --copy")
    os.system("autoheader --force")
    os.system("autoconf --force")
    os.system("automake -a --copy")

    if command.Command(['./configure',
                        '--prefix=%s'%path.prefix(),
                       ]).exec()==0:
      if make.exec("all")==0:
        if make.exec("install",parallelism=0.0)==0:
          self.OK = True
          self.manifest.touch()

    return self.OK

  ########

  def provide(self): ##########################################################

    if self.should_build:
      self.OK = self.build()
    print(self.OK)
    return self.OK
