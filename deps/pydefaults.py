from ork import dep, pip, path, dep
from ork.command import Command
###############################################################################

class pydefaults(dep.Provider):

  def __init__(self): ############################################
    super().__init__("pydefaults")
    build_dest = path.builds()/"pydefaults"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"pydefaults"
    self.OK = self.manifest.exists()
    self.python = self.declareDep("python")

  def build(self): ############################################################
      #PYTHON = dep.instance("python")
      pip.install(["pytest",
                   "numpy","scipy",
                   "numba","pyopencl",
                   "matplotlib",
                   "pyzmq","zlib"])
      ret = Command([self.python.executable,"-m","pip","install","--upgrade",
                     "Pillow","pysqlite3","jupyter","plotly","trimesh"]).exec()
      print(ret)
      return ret==0

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"numpy"/"LICENSE.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()
