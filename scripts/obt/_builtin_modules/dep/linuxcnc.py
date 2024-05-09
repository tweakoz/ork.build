###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command


deco = Deco()

###############################################################################

class linuxcnc(dep.Provider):

  def __init__(self): ############################################
    super().__init__("linuxcnc")
    self.source_root = path.builds()/"linuxcnc"
    self._archlist = ["x86_64"]

  def provide(self): ##########################################################
    dep.require("boost")
    pfx = path.prefix()
    git.Clone("https://github.com/linuxcnc/linuxcnc",self.source_root,"master")
    os.chdir(self.source_root/"src")
    #os.environ["INSTALL_PREFIX"] = str(path.prefix())
    os.environ["CXXFLAGS"]="-I%s"%(pfx/"include")
    os.environ["LDFLAGS"]="-L%s"%(pfx/"lib")
    os.environ["PKG_CONFIG_PATH"]="%s:/usr/lib/x86_64-linux-gnu/pkgconfig/:/usr/share/pkgconfig"%(pfx/"lib"/"pkgconfig")

    Command(["./autogen.sh"]).exec()

    #Command(["echo","${CXXFLAGS}"]).exec()
    #Command(["echo","${LDFLAGS}"]).exec()
    #Command(["echo","${PKG_CONFIG_PATH}"]).exec()

    Command(["./configure",
             "--with-realtime=uspace",
             "--enable-non-distributable=yes",
             "--with-boost-python=boost_python27-mt",
             "--prefix=%s"%pfx
             ]).exec()

    make.exec("LDFLAGS=${ORK_STAGING_FOLDER}/lib")
    self.manifest.touch()
    self.OK = self.manifest.exists()

    return self.OK
