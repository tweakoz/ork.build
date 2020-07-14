###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, path, command, env

###############################################################################

class parsertl14(dep.StdProvider):
  def __init__(self):
    name = "parsertl14"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/parsertl14",
                                      revision="master",
                                      recursive=False)
    #################################################
    srcroot = self.source_root
    #################################################
    class Builder(dep.BaseBuilder):
      def __init__(self,name):
        super().__init__(name)
      def build(self,srcdir,blddir,incremental=False):
        dep.require(self._deps)
        return True
      def install(self,blddir):
        return command.run([ "cp",
                             "-r",
                             srcroot/"include"/"parsertl",
                             path.includes()
                             ])==0
    #################################################
    self._builder = Builder(name)
