###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

dep.require("boost")

deco = Deco()
    
###############################################################################

class linuxcnc(dep.Provider):

  def __init__(self,options=None): ############################################


    parclass = super(linuxcnc,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"linuxcnc"
    self.source_dest = path.builds()/"linuxcnc"

    pfx = path.prefix()

    git.Clone("https://github.com/linuxcnc/linuxcnc",self.source_dest,"master")
    os.chdir(self.source_dest/"src")
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


  def provide(self): ##########################################################

      return self.OK

