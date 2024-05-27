###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v1.2.9"

import os, tarfile
from obt import dep, host, path, cmake, git, make, command, log, env
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class moltenvk(dep.Provider):

  def __init__(self): ############################################
    super().__init__("moltenvk")
    #print(options)
    self.source_root = path.builds()/"moltenvk"
    self.build_dest = path.builds()/"moltenvk"/".build"
    #self._archlist = ["x86_64"]
    self._oslist = ["Darwin"]
    self.sdk_dir = self.source_root/"Package"/"Latest"/"MoltenVK"
    self.build_lib_dir = self.sdk_dir/"dylib"/"macOS"
  def __str__(self): ##########################################################

    return "MoltenVK (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_root)
    os.system("rm -rf %s"%self.build_dest)

  def env_init(self):
    log.marker("registering Vulkan(%s) <MoltenVK> SDK"%VERSION)
    env.prepend("LD_LIBRARY_PATH",self.sdk_dir/"dylib")
    #env.append("PATH",self.sdk_dir/"bin")
    env.set("VULKAN_SDK",self.sdk_dir) # for cmake
    env.set("OBT_VULKAN_VERSION","MoltenVK-%s"%(VERSION)) # for OBT internal
    env.set("OBT_VULKAN_ROOT",self.sdk_dir) # for OBT internal
    env.set("VK_ICD_FILENAMES",self.build_lib_dir/"MoltenVK_icd.json")

  def build(self): ##########################################################

    #glfw = dep.require("glfw")

    if not self.source_root.exists():
      git.Clone("https://github.com/KhronosGroup/MoltenVK",self.source_root,VERSION)

    os.chdir(self.source_root)

    command.system(["./fetchDependencies --macos"])
    cmd = ["xcodebuild", "build", 
           "-project", '"MoltenVKPackaging.xcodeproj"',
           "-scheme", '"MoltenVK Package (macOS only)"',
           "-configuration", '"Debug"']
    ok = (0 == command.system(cmd))
    if ok:
      cmd = ["cp",self.build_lib_dir/"libMoltenVk.dylib",path.libs()/"libMoltenVk.dylib"]
      ok = (0 == command.system(cmd))
      if ok:
        cmd = ["cp","-r","Package/Latest/MoltenVK/include/*",path.includes()]
        ok = (0 == command.system(cmd))
        if ok:
          # moltenvlk does not automatically install shaderc
          cmd = ["brew","install","--overwrite", "shaderc"]
          ok = (0 == command.system(cmd))
    return ok

# Package/Debug/MoltenVKShaderConverter/Tools/MoltenVKShaderConverter <stage>/bin
