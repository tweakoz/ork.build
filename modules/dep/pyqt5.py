###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, host, git, command, env, log, pip

################################################################################
class pyqt5(dep.StdProvider):
  name = "pyqt5"
  ################################################################
  def __init__(self):
    super().__init__(pyqt5.name)
    self._archlist = ["x86_64"]
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,depmodule):
        super().__init__(pyqt5.name)
        self._depmodule = depmodule
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        qt = dep.require("qt5")
        ok = (0==pip.install("PyQt5==%s"%qt.fullver))
        if ok:
          # Remove PyQt's copy of Qt because we have our own.
          command.run(["rm","-rf",self._depmodule.pysite_dir/"Qt"])
        return ok
    #################################################
    self._builder = Builder(self)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.NopFetcher(pyqt5.name)
  ################################################################
  @property
  def pysite_dir(self):
    py = dep.instance("python")
    return py.site_packages_dir/"PyQt5"
  ################################################################
  def env_goto(self):
    return {
      "pyqt5": str(self.pysite_dir),
    }
  ########
  def wipe(self):
    qt = dep.instance("qt5")
    return (0==pip.uninstall("PyQt5==%s"%qt.fullver))
