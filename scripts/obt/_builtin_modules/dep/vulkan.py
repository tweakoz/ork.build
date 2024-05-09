###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "1.2.198.1"
MD5 = "c26c3febbf14faef595d7c26715a5472"

import os, tarfile
from obt import dep, host, path, cmake, git, make, command, wget, env, log, pathtools
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class _vulkan_from_lunarg(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vulkan")
    #print(options)
    self.fullver = VERSION
    self.source_root = path.builds()/"vulkan"
    self.build_dest = path.builds()/"vulkan"/".build"
    #self._archlist = ["x86_64"]
    self._oslist = ["Linux"]
    if host.IsX86_64:
      self.sdk_dir = self.source_root/VERSION/"x86_64"
    elif host.IsAARCH64:
      self.sdk_dir = self.source_root/VERSION/"aarch64"

  def __str__(self): ##########################################################

    return "Vulkan (lunarg-%s)" % VERSION

  ########################################################################
  @property
  def download_name(self):
    if host.IsX86_64:
      nam = "vulkansdk-linux-x86_64-%s.tar.gz"%VERSION
    elif host.IsX86_32:
      nam = "vulkansdk-linux-i386-%s.tar.gz"%VERSION
    elif host.IsAARCH64:
      nam = "vulkansdk-linux-aarch64-%s.tar.gz"%VERSION
    return nam 
  
  @property
  def download_URL(self):
    return "https://sdk.lunarg.com/sdk/download/%s/linux/%s"%(VERSION,self.download_name)

  @property
  def download_MD5(self):
    return MD5

  ########################################################################
  @property
  def revision(self):
    return VERSION
  #######################################################################

  def env_init(self):
    if self.sdk_dir.exists():
      log.marker("registering Vulkan(%s) SDK"%VERSION)
      env.prepend("LD_LIBRARY_PATH",self.sdk_dir/"lib")
      env.append("PATH",self.sdk_dir/"bin")
      env.set("VULKAN_SDK",self.sdk_dir) # for cmake
      env.set("VK_LAYER_PATH", self.sdk_dir/"etc"/"vulkan"/"explicit_layer.d")
      env.set("OBT_VULKAN_VERSION",VERSION) # for OBT internal
      env.set("OBT_VULKAN_ROOT",self.sdk_dir) # for OBT internal

  def areRequiredSourceFilesPresent(self):
    return (self.sdk_dir/".."/"setup-env.sh").exists()
  def areRequiredBinaryFilesPresent(self):
    return (self.sdk_dir/"bin"/"vkconfig").exists()

  def build(self): ##########################################################

    url = self.download_URL
    ok = wget(urls=[url],output_name=self.download_name,md5val=MD5)

    print(ok)
    if not ok:
      return False

    self.source_root.mkdir(parents=True,exist_ok=True)
    os.chdir(self.source_root)
    ok = (command.system(["rm","-rf",VERSION])==0)
    if not ok:
      return False
    ok = (command.system(["tar","xvf",path.downloads()/self.download_name])==0)
    if not ok:
      return False

    #samples_build_dir = self.sdk_dir/".."/"samples"/".build-samples"
    #pathtools.mkdir(samples_build_dir,clean=True)
    #samples_build_dir.chdir()
    #ok = (command.system(["cmake",".."])==0)
    #if not ok:
    #  return False
    #ok = (command.system(["make","-j",host.NumCores])==0)
    #if not ok:
    #  return False

    return True

###############################################################################

class _vulkan_from_system(dep.StdProvider):
  name = "vulkan"
  def __init__(self):
    super().__init__(_vulkan_from_system.name)
    self.fullver = "1.2.131"
    self._builder = dep.NopBuilder(_vulkan_from_system.name)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.NopFetcher(_vulkan_from_system.name)
  #######################################################################
  ########
  def __str__(self):
    return "vulkan"
  def env_init(self):
    log.marker("registering Vulkan(%s) SDK"%self.fullver)
    env.set("VULKAN_VER",self.fullver)
  def install_dir(self):
    return path.Path("/usr")

###############################################################################

if host.IsAARCH64:
  BASE = _vulkan_from_system
elif host.IsX86_64 or host.IsX86_32:
  BASE = _vulkan_from_lunarg
else:
  assert(False)

###############################################################################

class vulkan(BASE):
  def __init__(self):
    super().__init__()
  ########
  @property
  def include_dir(self):
    return path.include_dir()
