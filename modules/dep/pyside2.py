from obt import dep, pip, path, dep
from obt.command import Command
###############################################################################

class pyside2(dep.Provider):

  def __init__(self): ############################################
    super().__init__("pyside2")
    build_dest = path.builds()/"pyside2"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"pyside2"
    self.OK = self.manifest.exists()
    self.python = self.declareDep("python")

  def build(self): ############################################################
      return pip.install(["pyside2"])==0

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"PySide2"/"__init__.py").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()
