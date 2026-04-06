###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

LINUX_MD5 = "e054826ba9906af783c5109b5b618ec3"

import os, tarfile, glob
from obt import dep, host, path, cmake, git, make, command, wget, env, log, pathtools
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class _vulkan_from_moltenvk(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vulkan")
    self.VERSION = "v1.4.1"

    #print(options)
    self.source_root = path.builds()/"moltenvk"
    self.build_dest = path.builds()/"moltenvk"/".build"
    #self._archlist = ["x86_64"]
    self._oslist = ["Darwin"]
    self.sdk_dir = self.source_root/"Package"/"Latest"/"MoltenVK"
    self.build_lib_dir = self.sdk_dir/"dylib"/"macOS"
  def __str__(self): ##########################################################

    return "MoltenVK (github-%s)" % self.VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_root)
    os.system("rm -rf %s"%self.build_dest)

  def env_init(self):
    log.marker("registering Vulkan(%s) <MoltenVK> SDK"%self.VERSION)
    env.prepend("LD_LIBRARY_PATH",self.sdk_dir/"dylib")

    # DYLD_LIBRARY_PATH is still useful for ork.python-wrapped processes,
    # but C++ exes use glfwInitVulkanLoader() with an absolute dlopen of
    # $OBT_STAGE/lib/libvulkan.1.dylib to bypass SIP stripping.
    env.prepend("DYLD_LIBRARY_PATH", path.libs())
    env.append("DYLD_LIBRARY_PATH", path.macos_brew_lib)  # for validation layers and other deps

    env.set("VULKAN_SDK",self.sdk_dir) # for cmake
    env.set("OBT_VULKAN_VERSION","MoltenVK-%s"%(self.VERSION)) # for OBT internal
    env.set("OBT_VULKAN_ROOT",self.sdk_dir) # for OBT internal
    env.set("VK_ICD_FILENAMES",self.build_lib_dir/"MoltenVK_icd.json")

  def _build_vulkan_loader(self):
    """Build the Khronos Vulkan-Loader from source.

    Uses the Vulkan-Headers already fetched by MoltenVK (in External/)
    to build libvulkan.1.dylib — the Vulkan loader that discovers MoltenVK
    via the ICD mechanism. This eliminates the homebrew vulkan-loader dependency.
    """
    import subprocess, shutil

    headers_dir = self.source_root/"External"/"Vulkan-Headers"
    # determine the headers version tag for a matching loader checkout
    tag = subprocess.check_output(
      ["git","describe","--tags"],
      cwd=str(headers_dir)).decode().strip()
    log.marker("Building Vulkan-Loader %s to match MoltenVK headers" % tag)

    loader_src = path.builds()/"vulkan-loader"
    loader_build = loader_src/"build"
    if not loader_src.exists():
      git.Clone("https://github.com/KhronosGroup/Vulkan-Loader", loader_src, tag)
    else:
      command.run(["git","checkout",tag], working_dir=str(loader_src))

    loader_build.mkdir(parents=True, exist_ok=True)

    command.run([
      "cmake", str(loader_src),
      "-DCMAKE_BUILD_TYPE=Release",
      "-DVULKAN_HEADERS_INSTALL_DIR=%s" % headers_dir,
      "-DCMAKE_INSTALL_PREFIX=%s" % path.stage(),
      "-DBUILD_TESTS=OFF",
    ], working_dir=str(loader_build))

    command.run([
      "make", "-j%d" % os.cpu_count(),
    ], working_dir=str(loader_build))

    # install libvulkan.1.dylib + symlinks into staging lib
    for f in sorted(loader_build.glob("loader/libvulkan*")):
      dst = path.libs()/f.name
      if f.is_symlink():
        link_target = os.readlink(str(f))
        if dst.exists() or dst.is_symlink():
          dst.unlink()
        os.symlink(link_target, str(dst))
      else:
        shutil.copy2(str(f), str(dst))
    return True

  def build(self): ##########################################################

    #glfw = dep.require("glfw")

    if not self.source_root.exists():
      git.Clone("https://github.com/KhronosGroup/MoltenVK",self.source_root,self.VERSION)

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
        if ok:
          ok = self._build_vulkan_loader()
    return ok

###############################################################################

class _vulkan_from_lunarg(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vulkan")
    #print(options)
    self.VERSION = "1.3.296.0"
    self.fullver = self.VERSION
    self.source_root = path.builds()/"vulkan"
    self.build_dest = path.builds()/"vulkan"/".build"
    #self._archlist = ["x86_64"]
    self._oslist = ["Linux"]
    if host.IsX86_64:
      self.sdk_dir = self.source_root/self.VERSION/"x86_64"
    elif host.IsAARCH64:
      self.sdk_dir = self.source_root/self.VERSION/"aarch64"

  def __str__(self): ##########################################################

    return "Vulkan (lunarg-%s)" % self.VERSION

  ########################################################################
  @property
  def download_name(self):
    if host.IsX86_64:
      nam = "vulkansdk-linux-x86_64-%s.tar.xz"%self.VERSION
    elif host.IsX86_32:
      nam = "vulkansdk-linux-i386-%s.tar.xz"%self.VERSION
    elif host.IsAARCH64:
      nam = "vulkansdk-linux-aarch64-%s.tar.xz"%self.VERSION
    return nam 
  
  @property
  def download_URL(self):
    return "https://sdk.lunarg.com/sdk/download/%s/linux/%s"%(self.VERSION,self.download_name)

  @property
  def download_MD5(self):
    return LINUX_MD5

  ########################################################################
  @property
  def revision(self):
    return self.VERSION
  #######################################################################

  def env_init(self):
    if self.sdk_dir.exists():
      log.marker("registering Vulkan(%s) SDK"%self.VERSION)
      env.prepend("LD_LIBRARY_PATH",self.sdk_dir/"lib")
      env.append("PATH",self.sdk_dir/"bin")
      env.set("VULKAN_SDK",self.sdk_dir) # for cmake
      env.set("VK_LAYER_PATH", self.sdk_dir/"share"/"vulkan"/"explicit_layer.d")
      # restrict ICD to only the active GPU driver to avoid crashes
      # from unused ICDs pulling in libLLVM during dlopen
      _icd_dir = "/usr/share/vulkan/icd.d"
      _nvidia_icd = os.path.join(_icd_dir, "nvidia_icd.json")
      _radeon_icd = os.path.join(_icd_dir, "radeon_icd.x86_64.json")
      if os.path.exists(_nvidia_icd):
        env.set("VK_DRIVER_FILES", _nvidia_icd)
      elif os.path.exists(_radeon_icd):
        env.set("VK_DRIVER_FILES", _radeon_icd)
      env.set("OBT_VULKAN_VERSION",self.VERSION) # for OBT internal
      env.set("OBT_VULKAN_ROOT",self.sdk_dir) # for OBT internal

  def areRequiredSourceFilesPresent(self):
    return (self.sdk_dir/".."/"setup-env.sh").exists()
  def areRequiredBinaryFilesPresent(self):
    return (self.sdk_dir/"bin"/"vkconfig").exists()

  def build(self): ##########################################################

    url = self.download_URL
    ok = wget(urls=[url],output_name=self.download_name,md5val=LINUX_MD5)

    print(ok)
    if not ok:
      return False

    self.source_root.mkdir(parents=True,exist_ok=True)
    os.chdir(self.source_root)
    ok = (command.system(["rm","-rf",self.VERSION])==0)
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

if host.IsDarwin:
  BASE = _vulkan_from_moltenvk
elif host.IsAARCH64:
  BASE = _vulkan_from_lunarg
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
