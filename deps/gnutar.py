from yarl import URL
from ork import dep, path

###############################################################################

class gnutar(dep.StdProvider):
  def __init__(self):
    name = "gnutar"
    super().__init__(name)
    self._version = "1.34"
    self._fetcher = dep.WgetFetcher(name)
    baseurl = URL("ftp.gnu.org/gnu/tar")
    basename = "tar-%s"%self._version
    filename = "%s.tar.xz" % basename
    self.setSourceRoot(path.builds()/name/basename)
    self._fetcher._url = baseurl/filename
    self._fetcher._fname = filename
    self._fetcher._arctype = "tgz"
    self._fetcher._md5 = "9a08d29a9ac4727130b5708347c0f5cf"
    self._builder = dep.AutoConfBuilder(name)

    #src_dir = path.builds()/"ispc"/basename
    #dst_dir = path.stage()
    #self._builder.install_item(source=src_dir/"bin"/"ispc", \
    #                           destination=dst_dir/"bin"/"ispc")
  #def env_init(self):
   # log.marker("registering ispc(%s) SDK"%self._version)
    #env.set("ISPC",path.stage()/"bin"/"ispc")
