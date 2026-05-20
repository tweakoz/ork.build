###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class pybind11(dep.StdProvider):
  name = "pybind11"
  def __init__(self):
    super().__init__(pybind11.name)
    # High build_priority: pytorch (also priority 100) needs pybind11 done
    # before it can start, so pybind11 must clear the build queue ASAP —
    # front-load it alongside pytorch so the long-pole chain isn't gated
    # behind unrelated leaf deps.
    self.build_priority = 100
    self.declareDep("python")
    self.declareDep("cmake")
    PYTHON = dep.instance("python")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("PYTHON_EXECUTABLE",PYTHON.executable)
    # Install headers to $OBT_STAGE/include/obt.pybind11/pybind11/ instead of
    # the default $OBT_STAGE/include/pybind11/. Single, explicit, orkid-owned
    # location — consumers point a -I at $OBT_STAGE/include/obt.pybind11 and
    # nothing else can shadow it (in particular, pytorch's bundled pybind11
    # which lives under $OBT_PYPKG/torch/include/pybind11/ is invisible to
    # orkid because we copy torch headers to obt.torch/ excluding pybind11).
    self._builder.setCmVar("CMAKE_INSTALL_INCLUDEDIR","include/obt.pybind11")
    self._builder.requires(["python"])
    self._debug = True
    self._fetcher._debug = True
    self._builder._debug = True
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=pybind11.name,
                             repospec="pybind/pybind11",
                             revision="v3.0.4",   # Python 3.14 + subinterpreter support
                             md5val="73481f296ee0cbe1b84797a40ee6a93d",
                             recursive=False)
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"obt.pybind11"/"pybind11"/"attr.h").exists()
