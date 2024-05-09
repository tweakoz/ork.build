###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path
from obt.command import Command

###############################################################################

class nss(dep.StdProvider):
  name = "nss"
  def __init__(self):
    super().__init__(nss.name)
    self.setSourceRoot(path.builds()/"nss"/"source")
    ###########################################
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    
    nssdir = path.builds()/"nss"
    nss_source_dir = nssdir/"source"
    nss_dist_dir = nssdir/"dist"
    nss_nspr_dir = nssdir/"nspr"

    prep_command = Command(["./build.sh"],working_dir=nss_source_dir)
    clean_command = Command(["make"],working_dir=nss_source_dir)
    make_command = Command(["make"],working_dir=nss_source_dir)


    self._builder._cleanbuildcommands += [prep_command,clean_command,make_command]
    self._builder._incrbuildcommands += [prep_command,make_command]
    #assert(False) # WIP

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=nss.name,
                             repospec="nss-dev/nss",
                             revision="NSS_3_63_BRANCH",
                             recursive=False)
