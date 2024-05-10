###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, host, git, command, path, env
from obt.deco import Deco
deco = Deco()

class qt5ct(dep.StdProvider):
  name = "qt5ct"
  def __init__(self): ############################################
    super().__init__(qt5ct.name)
    self._archlist = ["x86_64"]
    #################################################
    srcroot = path.Path(self.source_root)
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,name):
        super().__init__(qt5ct.name)
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        (srcroot/"qt5ct").chdir()
        print(srcroot)
        env = {"PREFIX":path.stage()}
        ok = command.run([ "qmake"],env)==0
        if ok:
          # TODO: we MUST fix this SUDO!
          print(deco.red("WARNING THIS WILL WANT SUDO"))
          ok = command.run([ "sudo","make", "install"])==0
        return ok
    #################################################
    self._builder = Builder(qt5ct.name)
  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.SvnFetcher(qt5ct.name)
    fetcher._url = "svn://svn.code.sf.net/p/qt5ct/code"
    fetcher._revision = "trunk"
    return fetcher
  ########################################################################
