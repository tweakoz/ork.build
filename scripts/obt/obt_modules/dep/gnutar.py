from yarl import URL
from obt import dep, path

###############################################################################

class gnutar(dep.StdProvider):
  name = "gnutar"
  def __init__(self):
    super().__init__(gnutar.name)
    self._version = "1.34"
    baseurl = URL("ftp.gnu.org/gnu/tar")
    basename = "tar-%s"%self._version
    filename = "%s.tar.xz" % basename
    self.setSourceRoot(path.builds()/gnutar.name/basename)
    self._fetcher._url = baseurl/filename
    self._fetcher._fname = filename
    self._fetcher._arctype = "tgz"
    self._fetcher._md5 = "9a08d29a9ac4727130b5708347c0f5cf"
    self._builder = self.createBuilder(dep.AutoConfBuilder)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.WgetFetcher(gnutar.name)
  ########################################################################
