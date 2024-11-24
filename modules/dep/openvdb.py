###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, pathtools
###############################################################################
class openvdb(dep.StdProvider):
  name = "openvdb"
  def __init__(self):
    super().__init__(openvdb.name)
    self.declareDep("cmake")
    self.declareDep("blosc")
    self.declareDep("boost")
    self.declareDep("tbb")
    self.declareDep("nanobind")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON",
      "OPENVDB_BUILD_PYTHON_MODULE": "ON",
    }

  def onPostBuild(self):
    dep_python = dep.instance("python")
    deconame = dep_python._deconame
    st_lib = path.stage()/"lib"
    src_path = st_lib/deconame/"site-packages"
    dst_path = dep_python.pylib_dir/"site-packages"
    vcode = dep_python.version_major
    vcode = vcode.replace(".","")
    name = f"pyopenvdb.cpython-{vcode}-x86_64-linux-gnu.so"
    print(vcode)
    print(name)
    print(src_path/name)
    print(dst_path/name)
    pathtools.copyfile(src_path/name,dst_path/name)
    #pyopenvdb.cpython-312-x86_64-linux-gnu.so
    return True

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=openvdb.name,
                                repospec="AcademySoftwareFoundation/openvdb",
                                revision="v12.0.0",
                                recursive=False)
    return fetcher
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("openvdb").exists()
