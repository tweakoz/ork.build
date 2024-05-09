from obt import dep, pip, path, dep
from obt.command import Command
###############################################################################

class pyopengl(dep.Provider):

  def __init__(self): ############################################
    super().__init__("pyopengl")
    build_dest = path.builds()/"pyopengl"
    self.build_dest = build_dest
    self.python = self.declareDep("python")

  def build(self): ############################################################
      return pip.install(["pyopengl"])==0

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"PyOpenGL-3.1.5.dist-info").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()
