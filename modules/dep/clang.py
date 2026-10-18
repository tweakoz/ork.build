###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from pathlib import Path
import subprocess

from obt.dependency_artifacts import command_version
from obt import dep, host, path
from obt.command import Command

###############################################################################

class clang(dep.StdProvider):
  name = "clang"
  def __init__(self):
    super().__init__(self.name)
    self.llvm = self.declareDep("llvm")
    self.hostdesc = host.description()
    self.setSourceRoot(self.llvm.source_root)
    self.build_src = self.source_root/"clang"
    self.build_dest = self.source_root/".build-clang"
    self.build_working_dir = self.build_dest
    builder = self.createBuilder(dep.CMakeBuilder, static_libs=True, src_dir_override=self.build_src)
    builder.setCmVars({
      "LLVM_DIR": str(path.stage()/"lib"/"cmake"/"llvm"),
      "LLVM_LINK_LLVM_DYLIB": "ON",
      "CLANG_LINK_CLANG_DYLIB": "ON",
      "CLANG_INCLUDE_TESTS": "OFF",
      "LLVM_INCLUDE_TESTS": "OFF",
      "zstd_ROOT": str(path.stage()),
      "CMAKE_PREFIX_PATH": str(path.stage()),
      "CLANG_INCLUDE_DOCS": "OFF",
      "CLANG_ENABLE_STATIC_ANALYZER": "OFF",
      "CLANG_ENABLE_ARCMT": "OFF",
      "CMAKE_INSTALL_BINDIR": "bin",
      "CLANG_TOOLS_INSTALL_DIR": str(path.bin()),
      "LLVM_USE_SYMLINKS": "ON",
      "CLANG_LINKS_TO_CREATE": "ork.clang++-21;ork.clang-cpp-21",
    })
    if host.IsDarwin:
      # Upstream Clang does not infer Apple's selected SDK as Apple Clang does.
      # Use the same xcrun-selected SDK as OBT's CMAKE_OSX_SYSROOT.
      sysroot = Command(["xcrun", "--show-sdk-path"], do_log=False).capture().strip()
      builder.setCmVar("DEFAULT_SYSROOT", sysroot)
    builder.useMold()

  def build(self):
    # Preserve the exported clang target while prefixing only compiler drivers.
    patch = Path(__file__).parent/"patches"/"clang-21.1.8-orkid-prefix.patch"
    args = ["git", "apply", "--check", "--reverse", str(patch)]
    if subprocess.run(args, cwd=str(self.source_root), capture_output=True).returncode:
      subprocess.run(["git", "apply", "--check", str(patch)], cwd=str(self.source_root), check=True)
      subprocess.run(["git", "apply", str(patch)], cwd=str(self.source_root), check=True)
    return super().build()

  @property
  def bitcode_compiler(self):
    return path.bin()/"ork.clang++-21"

  @property
  def _fetcher(self):
    fetcher = dep.NopFetcher(self.name)
    fetcher._revision = self.llvm.version
    return fetcher

  def areRequiredSourceFilesPresent(self):
    return (self.build_src/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.bitcode_compiler.is_file()
            and any((path.libs()/name).is_file() for name in
                    ("libclang-cpp." + self.shlib_extension, "libclang-cpp.so.21.1"))
            and (path.includes()/"clang"/"Frontend"/"CompilerInstance.h").is_file()
            and command_version([self.bitcode_compiler, "--version"], self.llvm.version))

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()

  ##########################################
  @property
  def linux_bindir(self):
    if host.IsLinux:
      if host.IsGentoo:
        return path.Path("/usr/lib/llvm/11/bin")
      elif host.IsDebian:
        return path.Path("/usr/bin")
    return path.Path("")
  ##########################################
  @property
  def bin_clangpp(self):
   ub_release = {
      "bionic": "clang++-10",
      "buster": "clang++-13",
      "focal": "clang++-10",
      "jammy": "clang++-15",
      "mantic": "clang++-17",
      "noble": "clang++-18",
      "resolute": "clang++-21",
      "bookworm": "clang++-16",
   }
   if host.IsLinux:
      return self.linux_bindir/ub_release[self.hostdesc.codename]
   return path.Path("clang++")
  ##########################################
  @property
  def bin_clang(self):
   ub_release = {
      "bionic": "clang-10",
      "buster": "clang-11",
      "focal": "clang-10",
      "jammy": "clang-15",
      "mantic": "clang-17",
      "noble": "clang-18",
      "resolute": "clang-21",
      "bookworm": "clang-16",
   }
   if host.IsLinux:
     return self.linux_bindir/ub_release[self.hostdesc.codename]
   return path.Path("clang")
  ##########################################
