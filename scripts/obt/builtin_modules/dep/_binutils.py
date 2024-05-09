import obt

VER = "2.34"
HASH = "664ec3a2df7805ed3464639aaae332d6"

class context:
  def __init__(self,provider):
    self._archlist = ["x86_64"]
    self.name = "binutils-%s" % VER
    self.xzname = "%s.tar.xz" % self.name
    self.archive_file = obt.path.downloads()/self.xzname
    self.url = "https://ftp.gnu.org/gnu/binutils/%s"%self.xzname
    self.extract_dir = provider.build_src
    self.build_dir = provider.build_dest
    self.arcpath = obt.dep.downloadAndExtract([self.url],
                                               self.xzname,
                                               "xz",
                                               HASH,
                                               self.extract_dir)
