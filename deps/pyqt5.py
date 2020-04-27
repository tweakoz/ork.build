###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, host, git, command, env, log, pip

class pyqt5(dep.StdProvider):
  def __init__(self): ############################################
    name = "pyqt5"
    super().__init__(name)
    #################################################
    self._fetcher = dep.NopFetcher(name)
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self):
        super().__init__(name)
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        qt = dep.require("qt5")
        return 0==pip.install("PyQt5==%s"%qt.fullver)
    #################################################
    self._builder = Builder()
