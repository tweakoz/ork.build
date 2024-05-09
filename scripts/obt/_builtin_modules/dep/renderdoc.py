from obt import dep, pip, path, dep, pathtools, command, log, env
Command = command.Command

###############################################################################
VERSION = "1.28"
###############################################################################

class renderdoc(dep.Provider):

  def __init__(self): ############################################
    super().__init__("renderdoc")
    rdoc_dir = path.Path("/opt/renderdoc_%s"%VERSION)
    self.rdoc_dir = rdoc_dir
    self.rdoc_bin = rdoc_dir/"bin"/"qrenderdoc"
    self._oslist = ["Linux"]
    self._archlist = ["x86_64"]

  ########

  def build(self): ############################################################
      return 0

  ########

  def env_init(self):
    if self.rdoc_dir.exists():
      log.marker("registering renderdoc(%s) SDK"%VERSION)
      env.append("PATH",self.rdoc_dir/"bin")
      env.set("RENDERDOC_DIR",self.rdoc_dir)
      env.set("RENDERDOC_VER",VERSION)

  ########

  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "RENDERDOC",
                             environment = dict() )

  ########

  def areRequiredSourceFilesPresent(self):
    return self.rdoc_bin.exists()

  def areRequiredBinaryFilesPresent(self):
    return None
