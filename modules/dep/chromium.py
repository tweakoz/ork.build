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

class chromium(dep.StdProvider):
  name = "chromium"
  def __init__(self):
    super().__init__(chromium.name)
    #self._archlist = ["x86_64"]
  ##########################################
  def __str__(self):
    return "chromium(From git)"
  ##########################################
  @property
  def _fetcher(self):
    fetcher = dep.DepotToolsFetcher(chromium.name)
    fetcher._fetch_id = "chromium"
    return fetcher
  ##########################################
