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
    # MoltenVK build invokes the cmake binary (twice) inside
    # _build_vulkan_loader() to build Vulkan-Headers and Vulkan-Loader.
    # Without declaring cmake here, the parallel pipeline could schedule
    # vulkan to start before cmake has been installed to $OBT_STAGE/bin.
    # (The serial bootstrap path happened to work because MANDATORY_DEPS
    # processes [cmake, python, pydefaults, vulkan] in order, so cmake
    # was always done first by accident of iteration.)
    self.declareDep("cmake")
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
    # shutil.rmtree instead of os.system("rm -rf ...") — os.system inherits
    # the process's fd 1/2 directly, bypassing the per-thread log redirect
    # set up by obt.pipeline_io, and would leak output through the TUI.
    import shutil
    if self.source_root.exists():
      shutil.rmtree(str(self.source_root), ignore_errors=True)
    if self.build_dest.exists():
      shutil.rmtree(str(self.build_dest), ignore_errors=True)

  def env_init(self):
    log.marker("registering Vulkan(%s) <MoltenVK> SDK"%self.VERSION)
    env.prepend("LD_LIBRARY_PATH",self.sdk_dir/"dylib")

    # DYLD_LIBRARY_PATH is still useful for ork.python-wrapped processes,
    # but C++ exes use glfwInitVulkanLoader() with an absolute dlopen of
    # $OBT_STAGE/lib/libvulkan.1.dylib to bypass SIP stripping.
    env.prepend("DYLD_LIBRARY_PATH", path.libs())

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
    # determine the headers version tag for a matching loader checkout.
    # stderr=DEVNULL so git's noise can't leak through the TUI; we only
    # care about the captured stdout tag here.
    tag = subprocess.check_output(
      ["git","describe","--tags"],
      cwd=str(headers_dir),
      stderr=subprocess.DEVNULL).decode().strip()
    log.marker("Building Vulkan-Loader %s to match MoltenVK headers" % tag)

    loader_src = path.builds()/"vulkan-loader"
    loader_build = loader_src/"build"
    # GithubFetcher in tarball mode (recursive=False + default shallow=True)
    # re-extracts from the md5-cached tarball on every call, so the prior
    # "git checkout tag" else-branch is no longer needed — fetch() always
    # gives a clean tree at the requested revision.
    #
    # `tag` is computed from `git describe` on MoltenVK's bundled
    # Vulkan-Headers — deterministic given the pinned MoltenVK VERSION, so
    # the tarball md5 is stable and pinnable. md5val below is a HARVEST
    # placeholder: the first run fails at wget with "desired<0> actual<...>";
    # copy that actual hash in here to enable caching + validation.
    dep.GithubFetcher(name="vulkan-loader",
                      repospec="tweakoz/Vulkan-Loader",
                      revision=tag,
                      md5val="0",  # HARVEST: run once, read printed hash, pin here
                      recursive=False).fetch(loader_src)

    # cmake-install Vulkan-Headers so find_package(VulkanHeaders) works
    headers_build = headers_dir/".build"
    headers_build.mkdir(parents=True, exist_ok=True)
    headers_install = headers_dir/".install"
    command.run([
      "cmake", str(headers_dir),
      "-DCMAKE_INSTALL_PREFIX=%s" % headers_install,
    ], working_dir=str(headers_build))
    command.run(["make","install"], working_dir=str(headers_build))

    loader_build.mkdir(parents=True, exist_ok=True)

    command.run([
      "cmake", str(loader_src),
      "-DCMAKE_BUILD_TYPE=Release",
      "-DCMAKE_PREFIX_PATH=%s" % headers_install,
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
      # GithubFetcher tarball mode — md5-cached + validated. The guard
      # stays because the followup ./fetchDependencies + xcodebuild are
      # expensive; we only refetch when source_root is absent.
      dep.GithubFetcher(name="moltenvk",
                        repospec="tweakoz/MoltenVK",
                        revision=self.VERSION,
                        md5val="ba3285b89dfb4a633185f29e4d4cd30e", # v1.4.1
                        recursive=False).fetch(self.source_root)

    # No os.chdir(self.source_root) — racy under the parallel pipeline.
    # Each command.run() below sets working_dir explicitly.
    ok = (0 == command.run(["./fetchDependencies", "--macos"],
                            working_dir=self.source_root))
    if ok:
      ok = (0 == command.run(["xcodebuild", "build",
                              "-project", "MoltenVKPackaging.xcodeproj",
                              "-scheme", "MoltenVK Package (macOS only)",
                              "-configuration", "Debug"],
                              working_dir=self.source_root))
    if ok:
      ok = (0 == command.run(["cp",
                              str(self.build_lib_dir/"libMoltenVk.dylib"),
                              str(path.libs()/"libMoltenVk.dylib")]))
      if ok:
        # cp -r with a glob needs shell expansion; use a real glob.
        import glob, shutil as _sh
        src_dir = self.source_root/"Package"/"Latest"/"MoltenVK"/"include"
        ok = src_dir.exists()
        if ok:
          for entry in src_dir.iterdir():
            tgt = path.includes()/entry.name
            try:
              if entry.is_dir():
                _sh.copytree(str(entry), str(tgt), dirs_exist_ok=True)
              else:
                _sh.copy2(str(entry), str(tgt))
            except Exception as e:
              print("copy %s -> %s failed: %s" % (entry, tgt, e))
              ok = False
              break
        if ok:
          ok = self._build_vulkan_loader()
        if ok:
          # vk_enum_string_helper.h moved out of Vulkan-Headers into
          # Vulkan-Utility-Libraries in newer Vulkan SDKs. orkid still
          # includes it via <vulkan/vk_enum_string_helper.h>. Drop it in.
          ok = self._install_vk_enum_string_helper()
    return ok

  def _install_vk_enum_string_helper(self):
    """Fetch vk_enum_string_helper.h and install it to $OBT_STAGE/include/vulkan/.

    The helper file moved out of Vulkan-Headers into Vulkan-Utility-Libraries
    in newer Vulkan SDKs. We fetch the file at a tag that matches our
    MoltenVK-bundled Vulkan-Headers version, otherwise the helper references
    enum symbols that don't exist in our headers."""
    import subprocess
    headers_dir = self.source_root/"External"/"Vulkan-Headers"
    tag = subprocess.check_output(
      ["git","describe","--tags"],
      cwd=str(headers_dir),
      stderr=subprocess.DEVNULL).decode().strip()
    url = ("https://raw.githubusercontent.com/tweakoz/Vulkan-Utility-Libraries/"
           "%s/include/vulkan/vk_enum_string_helper.h" % tag)
    dst_dir = path.includes()/"vulkan"
    pathtools.ensureDirectoryExists(dst_dir)
    dst = dst_dir/"vk_enum_string_helper.h"
    log.marker("fetching vk_enum_string_helper.h @ %s" % tag)
    rc = command.run(["curl","-fsSL","-o",str(dst),url])
    return rc == 0

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
    # No chdir; pass working_dir to each subprocess. command.run instead
    # of command.system so output goes through the per-thread redirect.
    import shutil as _sh
    target = self.source_root/self.VERSION
    if target.exists():
      _sh.rmtree(str(target), ignore_errors=True)
    ok = (command.run(["tar","xvf",path.downloads()/self.download_name],
                       working_dir=self.source_root)==0)
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
