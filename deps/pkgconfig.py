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
    if self.manifest.exists():
        self.OK = True
        return

    extract_dir = path.builds()/"pkgconfig"
    source_dir = extract_dir/("pkg-config-%s" % VER)
    build_dir = source_dir/".build"

    url = "http://pkgconfig.freedesktop.org/releases/pkg-config-%s.tar.gz" % VER

    self.arcpath = dep.downloadAndExtract([url],
                                          "pkg-config-%s" % VER,
                                          "gz",
                                          HASH,
                                          extract_dir)


    os.mkdir(build_dir)
    os.chdir(build_dir)

    Command([ "../configure",
              "--prefix=%s"%path.prefix(),
              "--with-internal-glib"
             ]).exec()

    make.exec( "install" )
    self.manifest.touch()
    self.OK = True

  def provide(self): ##########################################################

      return self.OK
