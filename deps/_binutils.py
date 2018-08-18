import ork

VER = "2.30"
HASH = "ffc476dd46c96f932875d1b2e27e929f"

class context:
    def __init__(self,destid):
        self.name = "binutils-%s" % VER
        self.xzname = "%s.tar.xz" % self.name
        self.archive_file = ork.path.downloads()/self.xzname
        self.url = "https://ftp.gnu.org/gnu/binutils/%s"%self.xzname
        self.extract_dir = ork.path.builds()/destid
        self.build_dir = self.extract_dir/self.name

        self.arcpath = ork.dep.downloadAndExtract([self.url],
                                                   self.xzname,
                                                   "xz",
                                                   HASH,
                                                   self.extract_dir)

