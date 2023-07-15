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
###############################################################################
class yosys(dep.StdProvider):
  VERSION = "96b6410dcb7a82e7be8d4a2025835936f2ca84a7"
  NAME = "yosys"
  def __init__(self):
    super().__init__(yosys.NAME)
    self.declareDep("nextpnr")
    self.declareDep("arachnepnr")
    self.declareDep("icestorm")
    ###########################################
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    
    build_dir = path.builds()/yosys.NAME

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
    return dep.GithubFetcher(name=yosys.NAME,
                             repospec="YosysHQ/yosys",
                             revision=yosys.VERSION,
                             recursive=False)
  ########################################################################
