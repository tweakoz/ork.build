###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
from obt.command import Command
###############################################################################
class bazel(dep.StdProvider):
  name = "bazel"
  def __init__(self):
    super().__init__(bazel.name)
    from yarl import URL
    VER = "5.1.1"
    self.URLBASE = URL("https://releases.bazel.build/%s/release"%VER)
    self._fname = "bazel-%s-darwin-x86_64"%VER
    self._url = self.URLBASE/self._fname


    self._builder = self.createBuilder(dep.BinInstaller)

    self._builder.install_item(source=self.source_root/self._fname, 
                               destination=path.bin()/"bazel",
                               flags="ugo+x")

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.WgetFetcher(bazel.name)
    fetcher._fname = self._fname
    fetcher._url = self._url
    fetcher._arctype = "none"
    fetcher._md5 = "ed363c3e58e6fca9766bf0676ce4c53c"
    return fetcher
  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/self._fname).exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"share"/"pkgconfig"/"bazel3.pc").exists()

  def compileenv(self): ##########################################################
    return {
        "INCLUDE_PATH": path.includes()/"bazel3"
    }




