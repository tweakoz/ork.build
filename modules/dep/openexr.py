###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class openexr(dep.StdProvider):
  name = "openexr"
  def __init__(self):
    super().__init__(openexr.name)
    self.declareDep("cmake")
    self.declareDep("imath")
    self.declareDep("libdeflate")
    #self.declareDep("fltk")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("OPENEXR_VIEWERS_ENABLE","OFF")
    self._builder.setCmVar("CMAKE_MODULE_PATH",self.source_root)
    self._builder.setCmVar("PYILMBASE_ENABLE","OFF")
    # Force find_package to use the OBT-built imath / libdeflate, not
    # /opt/homebrew/opt/{imath,libdeflate}. Without these hints,
    # find_package finds the brew copies first on macOS.
    self._builder.setCmVar("Imath_ROOT",      str(path.prefix()))
    self._builder.setCmVar("Imath_DIR",       str(path.libs()/"cmake"/"Imath"))
    self._builder.setCmVar("libdeflate_ROOT", str(path.prefix()))
    self._builder.setCmVar("libdeflate_DIR",  str(path.libs()/"cmake"/"libdeflate"))
    # OpenEXR finds libdeflate via pkg_check_modules, not find_package, and
    # shadows CMAKE_IGNORE_PATH around that call. CMAKE_PREFIX_PATH is what
    # pins it: FindPkgConfig prepends <prefix>/lib/pkgconfig, so the staged
    # libdeflate.pc wins over /opt/homebrew's. The ignore list covers the
    # remaining find_* calls (same idiom as oiio.py).
    self._builder.setCmVar("CMAKE_PREFIX_PATH", str(path.prefix()))
    self._builder.setCmVar("CMAKE_IGNORE_PATH", "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include")
    #self._builder.requires(["fltk"])
    
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openexr.name,
                             repospec="tweakoz/openexr",
                             #revision="v2.5.8",
                             revision="obt-v3.2.1",
                             md5val="af9619821aee2044191b17ebb2e1273e",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libIlmImf.so").exists()
