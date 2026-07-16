###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class openxr(dep.StdProvider):
  name = "openxr"
  def __init__(self):
    super().__init__(openxr.name)
    self._archlist = ["x86_64", "aarch64"]
    self._oslist = ["Linux", "Darwin"]
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      # DYNAMIC_LOADER=ON builds the Khronos loader as a shared library
      # (libopenxr_loader). The loader discovers the runtime at run time
      # via XR_RUNTIME_JSON / active_runtime.json — orkid never names one.
      "DYNAMIC_LOADER": "ON",
      # Pin the libdir so the loader lands at <stage>/lib on every distro;
      # GNUInstallDirs otherwise picks lib64 on some Linux hosts.
      "CMAKE_INSTALL_LIBDIR": "lib",
      # Compile the SDK's vendored jsoncpp straight into the loader instead of
      # linking a host copy. Keeps the loader self-contained and deterministic;
      # a partial system JsonCpp cmake package otherwise resolves to
      # jsoncpp_lib-NOTFOUND at link time.
      "BUILD_WITH_SYSTEM_JSONCPP": "OFF",
    })
    # mold linker — Linux-only opt-in (no-op elsewhere). Called AFTER the
    # setCmVars above so the -fuse-ld=mold flags survive.
    self._builder.useMold()

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openxr.name,
                             repospec="KhronosGroup/OpenXR-SDK",
                             revision="release-1.1.60",
                             md5val="461700ee3e1ef925373ac9a3b36401dc",
                             recursive=False)
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/f"libopenxr_loader.{self.shlib_extension}").exists()
