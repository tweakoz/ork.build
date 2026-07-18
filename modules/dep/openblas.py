###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path, host
###############################################################################
class openblas(dep.StdProvider):
  VERSION ="v0.3.23"
  NAME = "openblas"
  def __init__(self):
    super().__init__(openblas.NAME)
    self.declareDep("cmake")    
    self._builder = dep.CMakeBuilder(openblas.NAME)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_EXAMPLES": "ON"
    })
    if host.IsX86_64:
      # Pin an AVX2 (HASWELL) baseline UNCONDITIONALLY on all x86_64 — never
      # autodetect the host core and never DYNAMIC_ARCH. Staged OpenBLAS
      # artifacts get consumed across the whole fleet, so a conservative,
      # portable target that runs everywhere beats per-box tuning (a
      # Zen5/Strix-Halo-tuned build would fault on older fleet members).
      self._builder.setCmVar("TARGET", "HASWELL")
    if host.IsLinux:
      # OpenBLAS-0.3.23's LAPACK glue (lapack/getrs/getrs_parallel.c) passes
      # a mismatched pointer to gemm_thread_n. gcc-14+ promotes
      # -Wincompatible-pointer-types (and -Wimplicit-function-declaration,
      # C23 default) to hard errors, breaking the build on gcc-15. Downgrade
      # those two classes back to warnings; the code is functionally correct.
      self._builder.setCmVar(
        "CMAKE_C_FLAGS",
        "-Wno-error=incompatible-pointer-types -Wno-error=implicit-function-declaration")
    if host.IsOsx:
     def postInstall():
       from obt import macos
       from obt.deco import Deco
       deco = Deco()
       print(deco.inf("Macos fixup dll installname for %s"% str(path.libs()/"libopenblas.dylib" )))
       macos.macho_change_id(path.libs()/"libopenblas.dylib","@rpath/libopenblas.0.dylib")
     self._builder._onPostInstall = postInstall

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openblas.NAME,
                             repospec="xianyi/OpenBLAS",
                             revision=openblas.VERSION,
                             md5val="4e30022e79990d5a6fa008e099a3ec56", # v0.3.23
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"openblas"/"lapacke.h").exists()

