###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class nsync_cpp(dep.StdProvider):
  name = "nsync_cpp"
  def __init__(self):
    super().__init__(nsync_cpp.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder,static_libs=True)
    self._builder.setCmVars({
    })
    self._builder._minimal = True

    #cmake ../tensorflow/lite -Dnsync_cpp_KERNEL_TEST=on -Dnsync_cpp_ENABLE_GPU=ON
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=nsync_cpp.name,
                             repospec="google/nsync",
                             revision="ac5489682760393fe21bd2a8e038b528442412a7",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libnsync_cppmcDynamics.so").exists()
