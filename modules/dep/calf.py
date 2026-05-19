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

    import shutil as _sh
    if self.source_root.exists():
      _sh.rmtree(str(self.source_root), ignore_errors=True)

    git.Clone("https://github.com/calf-studio-gear/calf",
              self.source_root,
              VERSION)

    # No chdir; each Command/make.exec runs in self.source_root via
    # working_dir. The autotools steps below previously used os.system
    # which inherits parent fd 1/2 (TUI leak) and process cwd (race).
    for autotools_cmd in (
        ["aclocal", "--force"],
        ["libtoolize", "--force", "--automake", "--copy"],
        ["autoheader", "--force"],
        ["autoconf", "--force"],
        ["automake", "-a", "--copy"],
    ):
      if command.Command(autotools_cmd, working_dir=self.source_root).exec() != 0:
        print(deco.red("calf: %s failed" % " ".join(autotools_cmd)))
        return False

    if command.Command(['./configure',
                        '--prefix=%s'%path.prefix(),
                       ], working_dir=self.source_root).exec()==0:
      if make.exec("all", working_dir=self.source_root)==0:
        if make.exec("install",parallelism=0.0,working_dir=self.source_root)==0:
          self.OK = True
          self.manifest.touch()

    return self.OK

  ########

  def provide(self): ##########################################################

    if self.should_build:
      self.OK = self.build()
    print(self.OK)
    return self.OK
