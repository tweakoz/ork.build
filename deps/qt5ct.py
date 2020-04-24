###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, host, git, command, path, env
from ork.deco import Deco
deco = Deco()

class qt5ct(dep.StdProvider):

  def __init__(self): ############################################
    name = "qt5ct"
    super().__init__(name)
    #################################################
    self._fetcher = dep.SvnFetcher(name)
    self._fetcher._url = "svn://svn.code.sf.net/p/qt5ct/code"
    self._fetcher._revision = "trunk"
    srcroot = path.Path(self.source_root)
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,name):
        super().__init__(name)
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
    self._builder = Builder(name)
