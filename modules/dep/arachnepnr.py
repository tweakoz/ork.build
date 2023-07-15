###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, host
from obt.command import Command
###############################################################################
class arachnepnr(dep.StdProvider):
  VERSION = "c40fb2289952f4f120cc10a5a4c82a6fb88442dc"
  NAME = "arachnepnr"
  def __init__(self):
    super().__init__(arachnepnr.NAME)
    self.declareDep("icestorm")
    ###########################################
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    
    build_dir = path.builds()/arachnepnr.NAME

    env = {
    	"PREFIX": path.stage()
    }

    make_clean_command = Command([
    	"make",
    	"-j",host.NumCores,
    	"clean","install"
    	],
    	working_dir=build_dir,
    	environment=env)

    make_incr_command = Command([
    	"make",
    	"-j",host.NumCores,
    	"install"],
    	working_dir=build_dir,
    	environment=env)

    self._builder._cleanbuildcommands += [make_clean_command]
    self._builder._incrbuildcommands += [make_incr_command]

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=arachnepnr.NAME,
                             repospec="cseed/arachne-pnr",
                             revision=arachnepnr.VERSION,
                             recursive=False)
  ########################################################################
