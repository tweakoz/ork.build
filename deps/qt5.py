###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

MAJOR_VERSION = "5.12"
MINOR_VERSION = "5"
HASH = "d8c9ed842d39f1a5f31a7ab31e4e886c"

import os, tarfile
from ork import dep, host, path, git, make, pathtools
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context as cmake_context
from yarl import URL

deco = Deco()

###############################################################################

class qt5(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(qt5,self)
    parclass.__init__(options=options)
    #print(options)
    self.manifest = path.manifests()/"qt5"
    self.OK = self.manifest.exists()
    self.baseurl = URL("http://mirror.os6.org/qtproject/official_releases/qt")
    self.fullver = "%s.%s" % (MAJOR_VERSION,MINOR_VERSION)
    self.name = "qt-everywhere-src-%s" % self.fullver
    self.xzname = "%s.tar.xz" % self.name
    self.url = self.baseurl/MAJOR_VERSION/self.fullver/"single"/self.xzname
    self.source_base = path.builds()/"qt5"
    self.source_dest = self.source_base/self.name
    self.build_dest = self.source_dest/".build"

  ########

  def __str__(self):
    return "QT5 (%s)" % self.name

  ########

  def download_and_extract(self): #############################################
    self.arcpath = dep.downloadAndExtract([self.url],
                                           self.xzname,
                                           "xz",
                                           HASH,
                                           self.source_base)

  ########

  def wipe(self):
    os.system("rm -rf %s"%self.source_dest)

  ########

  def build(self): ############################################################

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
        self.download_and_extract()

    #########################################
    # prep for build
    #########################################

    if self.incremental():
        os.chdir(self.build_dest)
    else:
        pathtools.mkdir(self.build_dest,clean=True)
        os.chdir(self.build_dest)

        options =  ["-prefix", path.qt5dir()]
        options += ["-c++std", "c++14", "-shared"]
        options += ["-opensource", "-confirm-license"]
        options += ["-nomake", "tests"]
        options += ["-opengl","desktop"]
        options += ["-debug"]

        if host.IsOsx:
          options += ["-qt-libpng","-qt-zlib","-no-framework"]
        else:
          options += ["-qt-xcb"]

        b = Command(["sh", "../configure"]+options)
        result = b.exec()

    #########################################
    # build
    #########################################

    make.exec(parallel=True)
    make.exec(parallel=True)
    # uhhuh - https://bugreports.qt.io/browse/QTBUG-60496
    return (0==make.exec(target="install", parallel=False))
