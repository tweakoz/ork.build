from obt import dep, pip, path, dep, pathtools, command, log, env
Command = command.Command
from yarl import URL
###############################################################################
VERSION = "2023.1"
###############################################################################

class vivado(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vivado")
    build_dest = path.builds()/"vivado"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"vivado"
    self.OK = self.manifest.exists()
    self.vivbase = path.vivado_base()/VERSION
    self._oslist = ["Linux"]
    self._archlist = ["x86_64"]

  ########

  def base(self):
      return self.vivbase

  def build(self): ############################################################
      return 0

  ########

  def env_init(self):
    log.marker("registering vivado(%s) SDK"%VERSION)
    env.append("PATH",self.vivbase/"bin")

  ########

  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "LITEX",
                             environment = dict() )

  ########

  def areRequiredSourceFilesPresent(self):
    return (self.vivbase/"bin"/"vivado").exists()

  def areRequiredBinaryFilesPresent(self):
    return None
