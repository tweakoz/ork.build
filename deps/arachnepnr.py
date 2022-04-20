###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path, host
from ork.command import Command
###############################################################################
class arachnepnr(dep.StdProvider):
  def __init__(self):
    name = "arachnepnr"
    super().__init__(name)
    self.declareDep("icestorm")
    self.VERSION = "c40fb2289952f4f120cc10a5a4c82a6fb88442dc"
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="cseed/arachne-pnr",
                                      revision=self.VERSION,
                                      recursive=False)
    ###########################################
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    
    build_dir = path.builds()/name

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

