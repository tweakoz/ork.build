###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import ork.dep
from ork.wget import wget
from ork.deco import Deco
from ork.command import Command
from pathlib import Path
from yarl import URL
import ork.path
import ork.host
import tarfile
import os

deco = Deco()

###########################################

class boost(ork.dep.Provider):

  ########

  def __init__(self,options=None):
    parclass = super(boost,self)
    parclass.__init__(options=options)
    self.version = "1_67_0"
    self.versiond = self.version.replace("_",".")
    self.baseurl = URL("https://dl.bintray.com/boostorg/release")
    self.fname = "boost_%s.tar.bz2"%self.version
    build_dest = ork.path.builds()/"boost"
    self.build_dest = build_dest
    self.OK = False
    self.reciept = ork.path.receipts()/"boost"

    if False==self.reciept.exists():
      self.download_and_extract()
      self.build()

  ########

  def download_and_extract(self):

    self.arcpath = wget( urls = [self.baseurl/self.versiond/"source"/self.fname],
                    output_name = self.fname,
                    md5val = "ced776cb19428ab8488774e1415535ab" )
    if self.arcpath:
      assert(tarfile.is_tarfile(self.arcpath))
      tf = tarfile.open(self.arcpath,mode='r:bz2')
      if self.build_dest.exists():
        Command(["rm","-rf",self.build_dest]).exec()
      self.build_dest.mkdir()
      print("extracting<%s> to build_dest<%s>"%(deco.path(self.arcpath),deco.path(self.build_dest)))
      tf.extractall(path=self.build_dest)

  ########

  def build(self):

    prefix = ork.path.prefix()
    toolset = "darwin" if ork.host.IsOsx \
         else "g++"

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

    linkflags = ["-stdlib=libc++"] if ork.host.IsOsx \
           else ["-stdlib=libstdc++"]

    c = Command(["./b2",
                 "--prefix=%s"%prefix,
                 "-d2",
                 "-j%d"%ork.host.NumCores,
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
      self.reciept.touch()

  def provide(self):
    return self.OK
