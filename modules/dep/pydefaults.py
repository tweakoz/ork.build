from obt import dep, pip, path, dep, host
from obt.command import Command
###############################################################################

class pydefaults(dep.Provider):

  def __init__(self): ############################################
    super().__init__("pydefaults")
    build_dest = path.builds()/"pydefaults"
    self.build_dest = build_dest
    self.python = self.declareDep("python")

  def build(self): ############################################################
    #PYTHON = dep.instance("python")
    pip.install(["pytest",
                  "numpy","scipy",
                  "numba","pyopencl",
                  "matplotlib",
                  "pyzmq",
                  "opencv-python"
                  #"ork.build" # okay...
                  ])#,"backports.lzma"])



    #################
    modules2 = ["Pillow","jupyter","plotly","trimesh","asciidoc", "pyudev", "playwright"]
    if host.IsDarwin == False:
      modules2 += ["pysqlite3"]
    #################

    ret = Command([self.python.executable,"-m","pip","install","--upgrade"]+modules2).exec()
    if ret != 0:
      print("pydefaults build ret<%d>"%int(ret))
      return False

    # playwright requires a separate browser install step
    ret2 = Command([self.python.executable,"-m","playwright","install","chromium"]).exec()
    print("pydefaults build ret<%d> playwright-install<%d>"%(int(ret),int(ret2)))
    return (ret2==0)

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"numpy"/"_globals.py").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()

###############################################################################
