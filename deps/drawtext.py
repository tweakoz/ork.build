from yarl import URL
from ork import dep, path

###############################################################################

class drawtext(dep.StdProvider):
  def __init__(self):
    name = "drawtext"
    super().__init__(name)
    self._archlist = ["x86_64"]
    self.VERSION = "v0.5"
    self.mustBuildInTree()
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="jtsiomb/libdrawtext",
                                      revision=self.VERSION,
                                      recursive=False)
    self._builder = self.createBuilder(dep.AutoConfBuilder)
  def areRequiredSourceFilesPresent(self):
    print(self.source_root)
    return (self.source_root/"configure").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libembree3.so").exists()
