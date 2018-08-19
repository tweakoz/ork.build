import ork

VER = "8.1.0"
HASH = "65f7c65818dc540b3437605026d329fc"

class context:
    def __init__(self,destid):
        self.version = VER
        self.name = "gcc-%s" % VER
        self.xzname = "%s.tar.xz" % self.name
        self.archive_file = ork.path.downloads()/self.xzname
        self.url = "https://ftp.gnu.org/gnu/gcc/gcc-%s/%s"%(VER,self.xzname)
        self.extract_dir = ork.path.builds()/destid
        self.build_dir = self.extract_dir/self.name

        self.arcpath = ork.dep.downloadAndExtract([self.url],
                                                   self.xzname,
                                                   "xz",
                                                   HASH,
                                                   self.extract_dir)

