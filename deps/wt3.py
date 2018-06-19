###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "3.3.9"
HASH = "e9fac6af4bc1245b63f36a691273526b"

import os, tarfile
from yarl import URL
from ork import dep, host, path
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

class wt3(dep.Provider):

    def __init__(self,options=None):
        self.dep_boost = dep.require("boost")
        parclass = super(wt3,self)
        parclass.__init__(options=options)
        print(options)
        build_dest = path.builds()/"wt3"
        self.build_dest = build_dest
        self.manifest = path.manifests()/"wt3"
        self.OK = self.manifest.exists()
        self.fname = "wt-%s.tar.gz"%VERSION
        if False==self.OK:
          self.download_and_extract()
          #self.OK = True
          #self.build()

    ########

    def download_and_extract(self):

        url = URL("https://github.com/emweb/wt/archive/%s/.tar.gz"%VERSION)

        self.arcpath = dep.downloadAndExtract([url],
                                              self.fname,
                                              "gz",
                                              HASH,
                                              self.build_dest)


    def build(self):
        pass

    def provide(self):
        return self.OK

