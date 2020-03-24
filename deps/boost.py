###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "1_67_0"
HASH = "ced776cb19428ab8488774e1415535ab"

import os,tarfile
from ork import path,host,dep
from ork.wget import wget
from ork.deco import Deco
from ork.command import Command
from pathlib import Path
from yarl import URL

deco = Deco()

###########################################

class boost(dep.Provider):

  ########

  def __init__(self):
    super().__init__()
    self.version = VERSION
    self.versiond = self.version.replace("_",".")
    self.baseurl = URL("https://dl.bintray.com/boostorg/release")
    self.fname = "boost_%s.tar.bz2"%self.version
    build_dest = path.builds()/"boost"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"boost"
    self.compiler = "clang++" if host.IsOsx else "g++"
    self.OK = self.manifest.exists()
    if self.option("force")==True:
      self.OK = False

  ########

  def __str__(self):
    return "Boost ver:%s" % VERSION

  ########

  def download_and_extract(self):

    self.arcpath = dep.downloadAndExtract([self.baseurl/self.versiond/"source"/self.fname],
                                          self.fname,
                                          "bz2",
                                          HASH,
                                          self.build_dest)

  ########

  def build(self):

    prefix = path.prefix()
    toolset = "darwin" if host.IsOsx \
         else "gcc"

    os.chdir(str(self.build_dest/("boost_"+self.version)))

    a = Command(["./bootstrap.sh",
                 "link=shared",
                 "runtime-link=shared",
                 "--prefix=%s"%prefix,
                 "toolset=%s" % toolset ]).exec()

    self.OK = (a==0)
    assert(self.OK)

    b = Command(["./b2",
                 "--prefix=%s"%prefix,
                 "toolset=%s" % toolset,
                 "link=shared",
                 "runtime-link=shared",
                 "headers"]).exec()

    self.OK = (b==0)
    assert(self.OK)

    cxxflags = ["-std=c++11","-fPIC"]

    linkflags = ['-rpath',str(path.prefix()/"lib")] if host.IsOsx \
           else ['-Wl,-rpath',str(path.prefix()/"lib")]

    if host.IsOsx:
      linkflags += ["-stdlib=libc++"]


    c = Command(["./b2",
                 "--prefix=%s"%prefix,
                 "-d2",
                 "-j%d"%host.NumCores,
                 "-sNO_LZMA=1",
                 "--layout=tagged",
                 "toolset=%s" % toolset,
                 "threading=multi",
                 "address-model=64",
                 'cxxflags=%s' % " ".join(cxxflags),
                 'linkflags=%s' % " ".join(linkflags),
                 "link=shared",
                 "runtime-link=shared",
                 "install"]).exec()

    #self.OK = (c==0)
    #assert(self.OK)

    if self.OK:
      self.manifest.touch()

  def provide(self):
    assert(False)
    if False==self.OK:
      self.download_and_extract()
      self.build()
    return self.OK
