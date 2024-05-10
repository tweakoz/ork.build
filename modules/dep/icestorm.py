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
class icestorm(dep.StdProvider):
  name = "icestorm"
  VERSION = "83b8ef947f77723f602b706eac16281e37de278c"
  def __init__(self):
    super().__init__(icestorm.name)
    ###########################################
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    
    build_dir = path.builds()/icestorm.name

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
    return dep.GithubFetcher(name=icestorm.name,
                             repospec="YosysHQ/icestorm",
                             revision=icestorm.VERSION,
                             recursive=False)

  #######################################################################
