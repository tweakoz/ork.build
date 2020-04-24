###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, host, git, command

class qt5forpython(dep.StdProvider):

  def __init__(self): ############################################
    name = "qt5forpython"
    super().__init__(name)
    #################################################
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "git://code.qt.io/pyside/pyside-setup.git"
    self._fetcher._revision = "5.14.1"
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,name):
        super().__init__(name)
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        cmd = [ "python3","./setup.py","install"]
        env = {
          "MAKEFLAGS":host.NumCores
        }
        return command.run(cmd,env)==0
    #################################################
    self._builder = Builder(name)
