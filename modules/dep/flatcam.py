###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, command

###############################################################################

class flatcam(dep.StdProvider):
  name = "flatcam"
  def __init__(self):
    super().__init__(flatcam.name)
    self._builder = self.createBuilder(dep.NopBuilder)
    self._modules  = ["tk","pyqt5","reportlab","svglib","vispy==0.7","pyopengl","rtree"]
    self._modules += ["rasterio","ezdxf","ortools","serial","numpy","shapely"]
    self._modules += ["lxml","cycler","python-dateutil","kiwisolver"]
    self._modules += ["dill","svg.path","freetype-py","fontTools","simplejson","qrcode"]
    self._buildcmd = ["make","install"]
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=flatcam.name,
                             repospec="tweakoz/flatcam",
                             revision="toz-obt2",
                             recursive=True)
  ########################################################################
  def on_build_shell(self):
    command.run(["pip3","install"]+self._modules)
    command.run(self._buildcmd)
    print( "run ./assets/linux/flatcam-beta")
    return command.subshell( directory=self.source_root,
                             prompt = "FLATCAM",
                             environment = dict() )
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"setup_ubuntu.sh").exists()
  def areRequiredBinaryFilesPresent(self):
    return (self.source_root/"assets"/"linux"/"flatcam-beta").exists()
