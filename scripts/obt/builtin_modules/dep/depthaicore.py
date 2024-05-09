###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, osrelease, host

###############################################################################

class depthaicore(dep.StdProvider):
  name = "depthaicore"
  def __init__(self):
    super().__init__(depthaicore.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON",
      "DEPTHAI_BUILD_TESTS": "ON",
    	"DEPTHAI_BUILD_EXAMPLES": "OFF"
    }
    desc = osrelease.descriptor()
    use_gcc_11 = desc.version_id == "23.10"
    use_gcc_11 = use_gcc_11 or (desc.version_id == "24.04")

    if use_gcc_11 and host.IsLinux:
      self._builder.setCmVar("CMAKE_CXX_COMPILER","g++-11")
      self._builder.setCmVar("CMAKE_C_COMPILER","gcc-11")

    # echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' | sudo tee /etc/udev/rules.d/80-movidius.rules
    # sudo udevadm control --reload-rules && sudo udevadm trigger
  
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=depthaicore.name,
                             repospec="tweakoz/depthai-core",
                             revision="main",
                             recursive=True)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libxxxx.so").exists()
