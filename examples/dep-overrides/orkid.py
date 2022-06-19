###############################################################################
# to activate, copy to ${OBT_STAGE}/dep-overrides/
###############################################################################
from ork import dep
###############################################################################
# get stock provider
###############################################################################
BASE = dep.module_class("orkid",with_overrides=False)
###############################################################################
class orkid(BASE):
  def __init__(self):
    super().__init__()
  #######################################################################
  # override fetcher , builder will be inherited for now...
  #######################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=orkid.name,
                                repospec="tweakoz/orkid",
                                revision="custombranch",
                                recursive=True,
                                shallow=False)
    fetcher._git_url = "ssh://git@customhost:customport/"+fetcher._repospec
    return fetcher
  #######################################################################
  # override description string
  #######################################################################
  def __str__(self):
    if hasattr(self,"descriptor"):
      return self.descriptor()
    else:
      return self._fetcher.descriptor()+":XXX"
