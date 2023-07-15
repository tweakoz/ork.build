###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, host, git, command, env, log

# OSX - brew install pyside

class qt5forpython(dep.StdProvider):
  name = "qt5forpython"
  def __init__(self): ############################################
    super().__init__(qt5forpython.name)
    self._archlist = ["x86_64"]
    #################################################
    self.major_version = "5.12" # todo get from qt
    self.minor_version = ""
    self.version = "%s%s" % (self.major_version,self.minor_version)
    #################################################
    srcroot = self.source_root
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,name):
        super().__init__(qt5forpython.name)
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        srcroot.chdir()
        llvm_dep = dep.require("llvm")
        cmd = [ "python3","./setup.py","install"]
        env = {
          "MAKEFLAGS":"-j %d"%host.NumCores,
          "CXX": "clang++",
          "CC": "clang",
          "LLVM_INSTALL_DIR": llvm_dep.install_dir()
        }
        return command.run(cmd,env)==0
    #################################################
    self._builder = Builder(qt5forpython.name)
  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(qt5forpython.name)
    fetcher._git_url = "git://code.qt.io/pyside/pyside-setup.git"
    fetcher._revision = self.version
    return fetcher
  ##############################################################################
  ## pyside
  ##############################################################################
  @property
  def pyside_dir(self):
    python_dep = dep.instance("python")
    pypkg = python_dep.site_packages_dir
    return pypkg/"PySide2"
  ##############################################################################
  @property
  def pyside_include_dir(self):
    return self.pyside_dir/"include"
  ##############################################################################
  @property
  def pyside_library_dir(self):
    return self.pyside_dir
  ##############################################################################
  @property
  def platform_lib_deco(self):
    if host.IsOsx:
      return "cpython-38d-darwin"
    else:
      return "cpython-38d-x86_64-linux-gnu"
  ##############################################################################
  @property
  def pyside_library(self):
    if host.IsOsx:
      return self.pyside_library_dir/("libpyside2.%s.5.12.%s"%(\
                                      self.platform_lib_deco,\
                                      self.shlib_extension))
    else:
      return self.pyside_library_dir/("libpyside2.%s.so.5.12"%self.platform_lib_deco)
  ##############################################################################
  def pyside_qtlibrary(self,name):
    if host.IsOsx:
      return self.pyside_library_dir/("%s.%s.%s"%(\
                                      name,\
                                      "cpython-38d-darwin",\
                                      "so"))#self.shlib_extension))
    else:
      return self.pyside_library_dir/("%s.%s.%s"%(\
                                      name,\
                                      self.platform_lib_deco,\
                                      self.shlib_extension))
  ##############################################################################
  @property
  def pyside_library_file(self):
    return self.pyside_library_dir/self.pyside_library
  ##############################################################################
  ## shiboken
  ##############################################################################
  @property
  def include_dir(self):
    python_dep = dep.instance("python")
    pypkg = python_dep.site_packages_dir
    rval =  pypkg/"shiboken2_generator/include"
    return rval
  ##############################################################################
  @property
  def library_path(self): ###########################################
    python_dep = dep.instance("python")
    pypkg = python_dep.site_packages_dir
    return pypkg/"shiboken2"
  ##############################################################################
  @property
  def library_file(self): ###########################################
    if host.IsOsx:
      #return self.library_path/("shiboken2.cpython-38d-darwin.so")
      return self.library_path/("libshiboken2.cpython-38d-darwin.%s.dylib"%self.major_version)
    else:
      return self.library_path/("libshiboken2.abi3.so.%s"%self.major_version)
  ##############################################################################
  @property
  def library_file2(self): ###########################################
    if host.IsOsx:
      return self.library_path/("libshiboken2.cpython-38d-darwin.%s.dylib"%self.major_version)
    else:
      return self.library_path/("libshiboken2.cpython-38d-x86_64-linux-gnu.so.%s"%self.major_version)
  ##############################################################################
  def env_init(self): ###########################################
    log.marker("registering qt5forpython SDK")
    env.append("LD_LIBRARY_PATH",self.pyside_dir)
    env.append("LD_LIBRARY_PATH",self.library_path)
  ##############################################################################
  def env_goto(self):
    return {
      "pyside2": str(self.pyside_dir),
    }
