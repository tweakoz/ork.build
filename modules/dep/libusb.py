###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libusb — pinned source build shared by macOS and Linux.
###############################################################################

VERSION  = "1.0.30"
BASENAME = "libusb-%s" % VERSION
FILENAME = "%s.tar.bz2" % BASENAME
URL_BASE = "https://github.com/libusb/libusb/releases/download/v%s" % VERSION
MD5      = "b0b0bacc2c6919515db8e863f0517db8"

from yarl import URL
from obt import dep, path


class libusb(dep.StdProvider):
  name = "libusb"

  def __init__(self):
    super().__init__(libusb.name)
    self.setSourceRoot(path.builds()/libusb.name/BASENAME)
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    self._builder._options += ["--disable-static"]

  def __str__(self):
    return "libusb (source-%s)" % VERSION

  @property
  def _fetcher(self):
    fetcher = dep.WgetFetcher(libusb.name)
    fetcher._url = URL(URL_BASE)/FILENAME
    fetcher._fname = FILENAME
    fetcher._arctype = "bz2"
    fetcher._md5 = MD5
    return fetcher

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"configure").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/("libusb-1.0.%s" % self.shlib_extension)).exists()

  @property
  def root(self):
    return path.prefix()

  @property
  def include_dir(self):
    return path.includes()/"libusb-1.0"

  @property
  def lib_dir(self):
    return path.libs()
