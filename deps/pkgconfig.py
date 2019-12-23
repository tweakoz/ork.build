import os, tarfile
from ork import dep, host, path, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

VER = "0.29.2"
HASH = "f6e931e319531b736fadc017f470e68a"

class pkgconfig(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(pkgconfig,self)
    parclass.__init__(options=options)

    self.manifest = path.manifests()/"yarl"
    self.extract_dir = path.builds()/"pkgconfig"
    self.source_dir = self.extract_dir/("pkg-config-%s" % VER)
    self.build_dir = self.source_dir/".build"
    self.url = "http://pkgconfig.freedesktop.org/releases/pkg-config-%s.tar.gz" % VER

    self.OK = self.manifest.exists()

  def build(self): ##########################################################

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

    if host.IsLinux:
        f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
        os.system( "rm -f %s" % f2r)

    self.OK = (make.exec( "install" )==0)
    if self.OK:
        self.manifest.touch()
    return self.OK

  def provide(self): ##########################################################
    if self.should_build():
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()
    return self.OK
