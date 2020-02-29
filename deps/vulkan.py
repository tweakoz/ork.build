###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "1.2.131.2"
MD5 = "bd3480e94ea7cf910ec4ba6b8022a681"

import os, tarfile
from ork import dep, host, path, cmake, git, make, command, wget
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class vulkan(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(vulkan,self)
    parclass.__init__(miscoptions=miscoptions)
    #print(options)
    self.source_dest = path.builds()/"vulkan"
    self.build_dest = path.builds()/"vulkan"/".build"
    self.manifest = path.manifests()/"vulkan"
    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "Vulkan (lunarg-%s)" % VERSION

  def build(self): ##########################################################
    nam = "vulkansdk-linux-x86_64-%s.tar.gz"%VERSION
    url = "https://sdk.lunarg.com/sdk/download/%s/linux/%s"%(VERSION,nam)
    wget(urls=[url],output_name=nam,md5val=MD5)
    self.source_dest.mkdir(parents=True,exist_ok=True)
    os.chdir(self.source_dest)
    ok = (command.system(["rm","-rf",VERSION])==0)
    ok = (command.system(["tar","xvf",path.downloads()/nam])==0)

    return True
