###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# Published under the GPL 2.0 license
###############################################################################
"""Open Image Denoise: CPU everywhere, Metal on Apple Silicon.

Linux GPU backends are opt-in: OBT_OIDN_CUDA=1 and/or OBT_OIDN_HIP=1.
They require system CUDA >=12.8 / ROCm >=6.4.2; the depper does not install
drivers or toolkits. CUDAToolkit_ROOT and ROCM_PATH select non-default roots.
"""
import os
import subprocess
import sys
from obt import dep, host, log, path

VERSION = "2.5.1"
BASENAME = "oidn-" + VERSION


class _Fetcher(dep.GithubFetcher):
  def __init__(self, cuda, hip):
    super().__init__(name="oidn", repospec="tweakoz/oidn",
                     revision="v" + VERSION, recursive=False, disable_tarball=True)
    self._modules = ["weights"]
    if cuda:
      self._modules.append("external/cutlass")
    if hip:
      self._modules.append("external/composable_kernel")

  def fetch(self, dest):
    # Resume a checkout if a previous submodule transfer was interrupted.
    if not (dest/".git").exists() and not super().fetch(dest):
      return False
    try:
      subprocess.run(["git", "lfs", "version"], check=True)
      # Upstream's relative URL would resolve to tweakoz/oidn-weights in a fork.
      subprocess.run(["git", "config", "submodule.weights.url",
                      "https://github.com/RenderKit/oidn-weights.git"], cwd=dest, check=True)
      subprocess.run(["git", "submodule", "update", "--init", "--depth", "1", "--"] + self._modules,
                     cwd=dest, check=True)
      # Also works when the outer environment deliberately skips LFS smudging.
      subprocess.run(["git", "lfs", "pull"], cwd=dest/"weights", check=True)
      return True
    except subprocess.CalledProcessError:
      print("OIDN fetch failed: check fork SSH access, Git LFS and submodule download logs")
      return False


def _enabled(name, default=False):
  value = os.environ.get(name, "1" if default else "0").lower()
  if value not in ("0", "1", "off", "on", "false", "true"):
    raise ValueError(name + " must be 0/1, off/on or false/true")
  return value in ("1", "on", "true")


class oidn(dep.StdProvider):
  name = "oidn"

  def __init__(self):
    super().__init__(self.name)
    self.setSourceRoot(path.builds()/self.name/BASENAME)
    self.declareDep("cmake")
    self.declareDep("tbb")
    ispc = self.declareDep("ispc")
    self._cuda = _enabled("OBT_OIDN_CUDA")
    self._hip = _enabled("OBT_OIDN_HIP")
    self._metal = _enabled("OBT_OIDN_METAL", host.IsOsx and host.IsAARCH64)
    if (self._cuda or self._hip) and not host.IsLinux:
      raise ValueError("OIDN CUDA/HIP backends require Linux in OBT")
    if self._metal and not (host.IsOsx and host.IsAARCH64):
      raise ValueError("OIDN Metal backend requires Apple Silicon")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    cmvars = {
      "OIDN_STATIC_LIB": "OFF",
      "OIDN_DEVICE_CPU": "ON",
      "OIDN_DEVICE_METAL": "ON" if self._metal else "OFF",
      "OIDN_DEVICE_CUDA": "ON" if self._cuda else "OFF",
      "OIDN_DEVICE_HIP": "ON" if self._hip else "OFF",
      "OIDN_DEVICE_SYCL": "OFF",
      "OIDN_FILTER_RT": "ON",
      "OIDN_FILTER_RTLIGHTMAP": "ON",
      "OIDN_APPS": "ON",
      "OIDN_APPS_OPENIMAGEIO": "OFF",
      "OIDN_INSTALL_DEPENDENCIES": "OFF",
      # Build-time blob conversion only; this does not build Python extensions.
      "Python_EXECUTABLE": sys.executable,
      "ISPC_EXECUTABLE": str(ispc.executable),
      "TBB_ROOT": str(path.stage()),
      "TBB_DIR": str(path.libs()/"cmake"/"TBB"),
      "CMAKE_PREFIX_PATH": str(path.stage()),
      "CMAKE_INSTALL_BINDIR": "bin",
      "CMAKE_INSTALL_LIBDIR": "lib",
      "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
    }
    if self._cuda:
      cmvars["OIDN_DEVICE_CUDA_API"] = "Driver"
      if os.environ.get("CUDAToolkit_ROOT"):
        cmvars["CUDAToolkit_ROOT"] = os.environ["CUDAToolkit_ROOT"]
    if self._hip:
      cmvars["ROCM_PATH"] = os.environ.get("ROCM_PATH", "/opt/rocm")
    self._builder.setCmVars(cmvars)

  @property
  def _fetcher(self):
    return _Fetcher(self._cuda, self._hip)

  def areRequiredSourceFilesPresent(self):
    required = ["CMakeLists.txt", "weights/rt_hdr.tza"]
    if self._cuda:
      required.append("external/cutlass/include/cutlass/cutlass.h")
    if self._hip:
      required.append("external/composable_kernel/include/ck/ck.hpp")
    if not all((self.source_root/name).exists() for name in required):
      return False
    # A checkout with unresolved Git LFS pointers is not usable source.
    return (self.source_root/"weights/rt_hdr.tza").stat().st_size > 1024

  def areRequiredBinaryFilesPresent(self):
    # Device modules are loaded dynamically; the front-end alone is incomplete.
    libs = ["OpenImageDenoise_core", "OpenImageDenoise_device_cpu"]
    libs += ["OpenImageDenoise_device_" + name for name, enabled in
             (("metal", self._metal), ("cuda", self._cuda), ("hip", self._hip)) if enabled]
    suffix = "." + VERSION + ".dylib" if host.IsOsx else ".so." + VERSION
    return (all((path.libs()/("lib" + name + suffix)).exists() for name in libs)
            and (path.libs()/("libOpenImageDenoise." + self.shlib_extension)).exists()
            and (path.bin()/"oidnDenoise").exists()
            and (path.includes()/"OpenImageDenoise"/"oidn.h").exists())

  def env_init(self):
    log.sdk_announce("registering Open Image Denoise SDK(%s)" % VERSION)

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()
