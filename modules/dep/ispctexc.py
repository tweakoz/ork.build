###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path, pathtools
from obt.command import Command
###############################################################################

class ispctexc(dep.StdProvider):
  name = "ispctexc"
  def __init__(self):
    super().__init__(ispctexc.name)
    self.declareDep("ispc")
    self.build_dest = self.source_root/"build"
    self._archlist = ["x86_64","aarch64"]

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=ispctexc.name,
                                repospec="tweakoz/ISPCTextureCompressor",
                                revision="master",
                                recursive=False)
    fetcher._cache=False
    return fetcher

  ########################################################################
  # the fork ships only Makefile.linux, whose defaults are x86-only
  #  (-msse2 for the c++ wrapper, --arch=x86-64 --target=sse2,avx for the kernels).
  # every one of those knobs is a `?=` variable except OBJS, and a command-line
  #  assignment beats a makefile assignment - so an aarch64 build needs no patched
  #  makefile and no fork commit, just overrides. the c++ wrappers contain zero SSE
  #  intrinsics (they only include the ispc-generated headers), so sse2neon is not
  #  needed here.
  ########################################################################

  def _make_vars(self):
    if not host.IsAARCH64:
      return [] # x86_64 uses the makefile as-is (unchanged, proven path)

    # single neon target: aarch64 has no runtime ISA dispatch, so there is no fat
    # dispatcher and only the base kernel objects exist. neon-i32x8 measured ~16%
    # faster than neon-i32x4 on apple m-series and emits byte-identical BC7 output.
    # narrow gangs (neon-i8x16 / neon-i16x8) do not compile these kernels.
    objs = ["ispc_texcomp/kernel_astc_ispc.o",
            "ispc_texcomp/kernel_ispc.o",
            "ispc_texcomp/ispc_texcomp_astc.o",
            "ispc_texcomp/ispc_texcomp.o"]

    cxx = "clang++" if host.IsOsx else "g++"
    cxxflags = "-O2 -fPIC -I."
    ispcflags = "-O2 --arch=aarch64 --target=neon-i32x8 --opt=fast-math --pic --woff"

    if host.IsOsx:
      ispcflags += " --target-os=macos"
      ldflags = "-shared -install_name @rpath/libispc_texcomp.so"
    else:
      ldflags = "-shared -rdynamic"

    return ["CXX=%s"%cxx,
            "ISPC=%s"%(path.stage()/"bin"/"ispc"),
            "CXXFLAGS=%s"%cxxflags,
            "ISPC_FLAGS=%s"%ispcflags,
            "LDFLAGS=%s"%ldflags,
            "OBJS=%s"%(" ".join(objs))]

  ########################################################################

  def build(self):

    dep.require("ispc")

    #########################################
    # fetch source
    #########################################

    if not self.source_root.exists():
      self._fetcher.fetch(self.source_root)

    #########################################
    # build
    #########################################

    self.source_root.chdir()
    r = Command(["make","-f","Makefile.linux"]+self._make_vars()).exec()
    OK = (r==0)

    if OK:
      OK = self.install()

    return OK

  def install(self):
    sonam = "libispc_texcomp.so"
    hdrnam = "ispc_texcomp.h"
    if host.IsOsx:
      cmd = ["install_name_tool",
             "-id","@rpath/libispc_texcomp.so",
             self.build_dest/sonam]
      Command(cmd).exec()
    pathtools.copyfile(self.build_dest/sonam,path.stage()/"lib"/sonam)
    pathtools.copyfile(self.source_root/"ispc_texcomp"/hdrnam,path.stage()/"include"/hdrnam)
    return True

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"Makefile.linux").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libispc_texcomp.so").exists()


