###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, host, git, command, env, log

class qt5forpython(dep.StdProvider):
  def __init__(self): ############################################
    name = "qt5forpython"
    super().__init__(name)
    #################################################
    self.major_version = "5.14" # todo get from qt
    self.minor_version = "1"
    self.version = "%s.%s" % (self.major_version,self.minor_version)
    #################################################
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "git://code.qt.io/pyside/pyside-setup.git"
    self._fetcher._revision = self.version
    srcroot = self.source_root
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,name):
        super().__init__(name)
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        srcroot.chdir()
        cmd = [ "python3","./setup.py","install"]
        env = {
          "MAKEFLAGS":"-j %d"%host.NumCores
        }
        return command.run(cmd,env)==0
    #################################################
    self._builder = Builder(name)
  ##############################################################################
  ## pyside
  ##############################################################################
  def pyside_dir(self):
    python_dep = dep.instance("python")
    pypkg = python_dep.site_packages_dir()
    return pypkg/"PySide2"
  ##############################################################################
  def pyside_include_dir(self):
    return self.pyside_dir()/"include"
  ##############################################################################
  def pyside_library_dir(self):
    return self.pyside_dir()
  ##############################################################################
  def pyside_library(self):
    return self.pyside_library_dir()/"libpyside2.cpython-38d-x86_64-linux-gnu.so.5.14"
    #return "%s.abi3.so"%name
  ##############################################################################
  def pyside_qtlibrary(self,name):
    return self.pyside_library_dir()/("%s.cpython-38d-x86_64-linux-gnu.so"%name)
    #return "%s.abi3.so"%name
  ##############################################################################
  def pyside_library_file(self):
    return self.pyside_library_dir()/self.pyside_library()
  ##############################################################################
  ## shiboken
  ##############################################################################
  def include_dir(self):
    python_dep = dep.instance("python")
    pypkg = python_dep.site_packages_dir()
    return pypkg/"shiboken2_generator/include"
  def library_path(self): ###########################################
    python_dep = dep.instance("python")
    pypkg = python_dep.site_packages_dir()
    return pypkg/"shiboken2"
  def library_file(self): ###########################################
    return self.library_path()/("libshiboken2.abi3.so.%s"%self.major_version)
  def library_file2(self): ###########################################
    return self.library_path()/("libshiboken2.cpython-38d-x86_64-linux-gnu.so.%s"%self.major_version)
  def env_init(self): ###########################################
    log.marker("registering qt5forpython SDK")
    env.append("LD_LIBRARY_PATH",self.pyside_dir())
    env.append("LD_LIBRARY_PATH",self.library_path())
  def env_goto(self):
    return {
      "pyside2": str(self.pyside_dir()),
    }
