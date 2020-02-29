###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from ork import dep, host, path, cmake, git, make, command, pathtools, patch
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

dep.require("ispc")

###############################################################################

class ispctexc(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(ispctexc,self)
    parclass.__init__(miscoptions=miscoptions)
    #print(options)
    self.source_dest = path.builds()/"ispctexc"
    self.build_dest = path.builds()/"ispctexc"/"build"
    self.manifest = path.manifests()/"ispctexc"
    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "ISPCTextureCompressor (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_dest)

  def build(self): ##########################################################

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
        git.Clone("https://github.com/GameTechDev/ISPCTextureCompressor",self.source_dest,VERSION)

    #########################################
    # build
    #########################################

    self.source_dest.chdir()

    ENV = {
        "ISPC": path.stage()/"bin"/"ispc"
    }
    r = Command(["make","-f","Makefile.linux"],environment=ENV).exec()
    self.OK = (r==0)
    if self.OK:
      sonam = "libispc_texcomp.so"
      hdrnam = "ispc_texcomp.h"
      pathtools.copyfile(self.build_dest/sonam,path.stage()/"lib"/sonam)
      pathtools.copyfile(self.source_dest/"ispc_texcomp"/hdrnam,path.stage()/"include"/hdrnam)

    return self.OK
