from yarl import URL
from obt import dep, path

###############################################################################

class drawtext(dep.StdProvider):
  VERSION = "v0.5"
  name = "drawtext"
  def __init__(self):
    super().__init__(drawtext.name)
    self._archlist = ["x86_64"]
    self.mustBuildInTree()
    self._builder = self.createBuilder(dep.AutoConfBuilder)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=drawtext.name,
                             repospec="jtsiomb/libdrawtext",
                             revision=drawtext.VERSION,
                             recursive=False)

  #######################################################################

  def areRequiredSourceFilesPresent(self):
    print(self.source_root)
    return (self.source_root/"configure").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libembree3.so").exists()
