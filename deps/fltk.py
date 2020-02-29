###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, command, path


###############################################################################

class fltk(dep.StdProvider):
  #############################################
  def __init__(self,miscoptions=None):
    name = "fltk"
    parclass = super(fltk,self)
    parclass.__init__(name,miscoptions=miscoptions)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/fltk/fltk"
    self._fetcher._revision = "release-1.3.5"
    self._builder = dep.CMakeBuilder(name)
  #############################################
  def install(self):
    ok = self._builder.install(self.build_dest)
    if ok:
      ok = (0==command.system(["rm",path.libs()/"libfltk*.a"]))
    return ok
  #############################################
