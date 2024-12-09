###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, pathtools, host, macos
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
    self.declareDep("llvm")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    dep_python = dep.instance("python")
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON",
      "OPENVDB_BUILD_PYTHON_MODULE": "ON",
      "OPENVDB_BUILD_AX": "ON",
      "LLVM_ROOT": path.stage(),
      "CMAKE_FIND_DEBUG_MODE": "OFF",
      "PYTHON_EXECUTABLE": path.pyvenv/"bin"/"python3",
      "PYTHON_LIBRARY": path.pyvenv/"lib"/dep_python.library_file,
      "Python_FIND_STRATEGY": "LOCATION",
      "Python_ROOT_DIR": path.pyvenv,
      "VDB_PYTHON_INSTALL_DIRECTORY": path.pyvenv/"lib"/dep_python._deconame/"site-packages",
    }

  def onPostInstall(self):
    dep_python = dep.instance("python")
    deconame = dep_python._deconame
    st_lib = path.stage()/"lib"
    pyext_dst_path = dep_python.pylib_dir/"site-packages"
    vcode = dep_python.version_major
    vcode = vcode.replace(".","")
    platform = "darwin" if host.IsDarwin else "x86_64-linux-gnu"
    print(vcode)
    if host.IsDarwin:
      pyext_src_path = self.build_dest/"openvdb"/"openvdb"/"python"
      src_name = f"openvdb.cpython-{vcode}-{platform}.so"
      dst_name = src_name      
      pyext_src_path = pyext_src_path/src_name
      pyext_dst_path = pyext_dst_path/dst_name
    else:
      pyext_src_path = st_lib/deconame/"site-packages"
      src_name = f"openvdb.cpython-{vcode}-{platform}.so"
      dst_name = src_name
      pyext_src_path = pyext_src_path/src_name
      pyext_dst_path = pyext_dst_path/dst_name
    print(pyext_src_path)
    print(pyext_dst_path)
    pathtools.copyfile(pyext_src_path,pyext_dst_path)
    if host.IsDarwin:
      macos.macho_replace_loadpaths(pyext_dst_path,"@executable_path/../lib","@rpath")
      macos.macho_replace_loadpaths(pyext_dst_path,"libboost_iostreams-mt-a64.dylib","@rpath/libboost_iostreams-mt-a64.dylib")
      macos.macho_dump(pyext_dst_path)
      dll = path.stage()/"lib"/"libopenvdb.dylib"
      macos.macho_replace_loadpaths(dll,"libboost_iostreams-mt-a64.dylib","@rpath/libboost_iostreams-mt-a64.dylib")
      macos.macho_dump(dll)

    return True

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=openvdb.name,
                                repospec="tweakoz/openvdb",
                                revision="toz-2024-v12-obt",
                                recursive=True)
    return fetcher
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("openvdb").exists()
