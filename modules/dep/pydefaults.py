from obt import dep, pip, path, dep, host
from obt.command import Command
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
                  "pyzmq",
                  #"ork.build" # okay...
                  ])#,"backports.lzma"])



    #################
    modules2 = ["Pillow","jupyter","plotly","trimesh","asciidoc", "pyudev"]
    if host.IsDarwin == False:
      modules2 += ["pysqlite3"]
    #################

    ret = Command([self.python.executable,"-m","pip","install","--upgrade"]+modules2).exec()

    print("pydefaults build ret<%d>"%int(ret))
    return (ret==0)

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"numpy"/"_globals.py").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()

###############################################################################
