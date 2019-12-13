import os, tarfile
from ork import dep, host, path, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

VER = "0.28"
HASH = "aa3c86e67551adc3ac865160e34a2a0d"

class pkgconfig(dep.Provider):

  def __init__(self,options=None): ############################################

    self.manifest = path.manifests()/"yarl"
    self.extract_dir = path.builds()/"pkgconfig"
    self.source_dir = self.extract_dir/("pkg-config-%s" % VER)
    self.build_dir = self.source_dir/".build"
    self.url = "http://pkgconfig.freedesktop.org/releases/pkg-config-%s.tar.gz" % VER

    if "force" in options and options["force"]==True:
      pass

    elif self.manifest.exists():
        self.OK = True
        return

  def provide(self): ##########################################################

    self.arcpath = dep.downloadAndExtract([self.url],
                                          "pkg-config-%s" % VER,
                                          "gz",
                                          HASH,
                                          self.extract_dir)


    os.mkdir(self.build_dir)
    os.chdir(self.build_dir)

    Command([ "../configure",
              "--prefix=%s"%path.prefix(),
              "--with-internal-glib"
             ]).exec()

    #assert(False)

    make.exec( "install" )
    self.manifest.touch()
    self.OK = True
    return self.OK
