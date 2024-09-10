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
    modules = [ "numpy",
                "scipy",
                "numba",
                "pyopencl",
                "matplotlib",
                "pyzmq",
                "mido",
                "ipython",
                "traitlets",
                "imgui_bundle",
                "PyGLM",
                "opencv-contrib-python",
                "solidpython2",
                # "manifold3d", # TODO: disable on aarch64/linux
                "scikit-image",
                "MDAnalysis",
                "MDAnalysisData",
                #"cadquery[ipython]" # does not work on macos/arm64
              ]
    modules += ["Pillow","jupyter","plotly","trimesh","asciidoc"]
    if host.IsDarwin == False:
      modules += ["pysqlite3","pyudev"]
    #################

    ret = Command([self.python.executable,"-m","pip","install","--upgrade"]+modules).exec()

    print("pydefaults build ret<%d>"%int(ret))
    return (ret==0)

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"numpy"/"_globals.py").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()

###############################################################################
