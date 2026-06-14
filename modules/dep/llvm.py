###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path
from obt.command import Command
from obt import log
from obt.deco import Deco
deco = Deco()

class _llvm_from_source(dep.StdProvider):
  name = "llvm"
  def __init__(self,name):
    super().__init__(_llvm_from_source.name)
    self._archlist = ["x86_64","aarch64"]
    ##########################################
    # llvm cmake file is 1 subdir deeper than usual
    ##########################################
    self.build_src = self.source_root/"llvm"
    self.build_dest = self.source_root/".build"
    ##########################################
    self._builder = self.createBuilder(
      dep.CMakeBuilder,
      src_dir_override=self.build_src)
    self.declareDep("zstd")
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        # Aggregate libLLVM.dylib so downstream consumers (e.g. OpenVDB AX)
        # link a single library instead of an exact per-component list that
        # drifts between LLVM versions. LLVM forbids combining BUILD_SHARED_LIBS
        # with LLVM_LINK_LLVM_DYLIB, so per-component libs stay static and roll
        # up into the single aggregate dylib.
        "BUILD_SHARED_LIBS": "OFF",
        "LLVM_BUILD_LLVM_DYLIB": "ON",
        "LLVM_LINK_LLVM_DYLIB": "ON",
        "LLVM_INSTALL_UTILS": "ON",
        "LLVM_ENABLE_DUMP": "ON",
        # Force-on so cmake fails loudly if the OBT-built zstd is missing
        # rather than silently falling back to a system path.
        "LLVM_ENABLE_ZSTD": "FORCE_ON",
        "zstd_ROOT": str(path.prefix()),
        #"LLVM_ENABLE_PROJECTS": "clang;libcxx;libcxxabi"
    })
    # arm64-apple-darwin24.1.0
    if host.IsAARCH64:
      self._builder.setCmVar("LLVM_TARGETS_TO_BUILD","AArch64")
    else:
      self._builder.setCmVar("LLVM_TARGETS_TO_BUILD","X86")
    # mold linker — biggest single win in the dep set; LLVM's final link
    # of libLLVM/libclang + tools is one of the slowest link phases.
    # Linux-only; no-op on macOS.
    self._builder.useMold()

  ########################################################################
  @property
  def _fetcher(self):
    # md5val enables wget's download cache for the github tarball — without
    # it wget re-downloads the ~166 MB llvm tarball on every provision.
    # NOTE: the md5 pins tarball *content*. If toz-apr20 is a branch and
    # gets new commits, this hash must be recomputed or the fetch will
    # hard-fail (wget returns None on md5 mismatch, not just a cache miss).
    fetcher = dep.GithubFetcher(name=_llvm_from_source.name,
                                repospec="tweakoz/llvm-project",
                                revision="toz-2026-may23",
                                md5val="3863ed18b96116b4611276211d6712a1",
                                recursive=False)
    return fetcher
  ########################################################################

  def install_dir(self):
    return path.stage()

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"bin"/"llvm-cov").exists()

###############################################################################

class _llvm_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
  def install_dir(self):
    return path.Path("/usr/local/opt/llvm")

###############################################################################

BASE = _llvm_from_source

###############################################################################

class llvm(BASE):
  def __init__(self):
    super().__init__("llvm")
  def env_init(self):
    log.sdk_announce("registering LLVM SDK")
