###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, pathtools, wget, env
from obt.deco import Deco 
deco = Deco()
###############################################################################
class astrocom(dep.StdProvider):
  NAME = "astrocom"
  def __init__(self):
    super().__init__(astrocom.NAME)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    self.build_dir = path.builds()/astrocom.NAME
    self.share_dir = path.share()/"astro"
    env = {
    	"PREFIX": path.stage()
    }

    def grab_starmaps():
      print(deco.yellow("fetching starmap data [2GPixel]"))
      pathtools.mkdir(self.share_dir)
      smap_2G = wget.wget(urls=["https://svs.gsfc.nasa.gov/vis/a000000/a004800/a004851/starmap_2020_64k.exr"],
                           output_name=self.share_dir/"starmap_2020_64k.exr",
                           md5val="9f49029b21949fa57d6915868295d920")
      print(deco.yellow("fetching starmap data [512Mpixel]"))
      smap_512M = wget.wget(urls=["https://svs.gsfc.nasa.gov/vis/a000000/a004800/a004851/starmap_2020_32k.exr"],
                           output_name=self.share_dir/"starmap_2020_32k.exr",
                           md5val="726edf8a69b805379241cc5dc54653cd")
      print(deco.yellow("fetching starmap data [128Mpixel]"))
      smap_128M = wget.wget(urls=["https://svs.gsfc.nasa.gov/vis/a000000/a004800/a004851/starmap_2020_16k.exr"],
                           output_name=self.share_dir/"starmap_2020_16k.exr",
                           md5val="761e43a304db583f7d3955b57680fa8e")
      print(deco.yellow("fetching starmap data [8Mpixel]"))
      smap_8M = wget.wget(urls=["https://svs.gsfc.nasa.gov/vis/a000000/a004800/a004851/starmap_2020_4k.exr"],
                           output_name=self.share_dir/"starmap_2020_4k.exr",
                           md5val="eac33e4c28e42cfdb8dc26b3b9a7eefb")


      print(deco.yellow("fetching halpha healpix map"))
      halpha_map_1K = wget.wget(urls=["https://faun.rc.fas.harvard.edu/dfink/skymaps/halpha/data/v1_1/healpix/Halpha_fwhm06_1024.fits"],
                                output_name=self.share_dir/"Halpha_fwhm06_1024.fits",
                                md5val="7aca800d81a6cf1609dea08850b48c32")
      
      print(deco.yellow("fetching halpha healpix mask"))
      halpha_mask_1K = wget.wget(urls=["https://faun.rc.fas.harvard.edu/dfink/skymaps/halpha/data/v1_1/healpix/Halpha_mask_fwhm06_1024.fits"],
                                 output_name=self.share_dir/"Halpha_mask_fwhm06_1024.fits",
                                 md5val="95a675d45b06cfd03500a7e02e1974fc")
      
      print(deco.yellow("fetching halpha healpix error"))
      halpha_error_1K = wget.wget(urls=["https://faun.rc.fas.harvard.edu/dfink/skymaps/halpha/data/v1_1/healpix/Halpha_error_fwhm06_1024.fits"],
                                  output_name=self.share_dir/"Halpha_error_fwhm06_1024.fits",
                                  md5val="612d560c9b3ebe4ea2d8b18f6ef26c1f")
      
      print(deco.yellow("fetching halpha fullsky map"))
      halpha_map_32M = wget.wget(urls=["https://faun.rc.fas.harvard.edu/dfink/skymaps/halpha/data/v1_1/maps/Halpha_map.fits"],
                                 output_name=self.share_dir/"Halpha_map.fits",
                                 md5val="c174b17ca83922910ea21a9ead84ef8b")
      
      print(deco.yellow("fetching halpha fullsky mask"))
      halpha_mask_32M = wget.wget(urls=["https://faun.rc.fas.harvard.edu/dfink/skymaps/halpha/data/v1_1/maps/Halpha_mask.fits"],
                                  output_name=self.share_dir/"Halpha_mask.fits",
                                  md5val="7a832c8549c3b8f6a6fb36541b255278")
      
      print(deco.yellow("fetching halpha fullsky error"))
      halpha_error_32M = wget.wget(urls=["https://faun.rc.fas.harvard.edu/dfink/skymaps/halpha/data/v1_1/maps/Halpha_error.fits"],
                                   output_name=self.share_dir/"Halpha_error.fits",
                                   md5val="679aa35be7f2c7a531859f0f29010f7e")
                      
    cmdlist_incr = []
    cmdlist_incr += [ dep.CustomStep("grab field", grab_starmaps) ]

    self._builder._incrbuildcommands = cmdlist_incr
    self._builder.setEnvVars(env)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=astrocom.NAME,
                             repospec="tweakoz/AstroComPYute",
                             revision="toz-2024-ub24",
                             recursive=True)

  ########################################################################
  def env_init(self):
    env.set("OBT_ASTROREF_DATA",self.share_dir)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()
  
