VERSION = "19.0"

from obt import dep, host, path, git, pathtools, command, patch, env
from obt import log

class houdini(dep.Provider):
  def __init__(self): ############################################
    super().__init__("houdini")
    #print(options)
    self.hfs_vers = "hfs%s"%VERSION
    self.hfs_path = path.Path("/opt")/self.hfs_vers
    self.source_root = path.builds()/"houdini"
    self.build_dest = self.source_root
    self.header_dest = path.prefix()/"include"/"houdini"

    #############################

    @property
    def manifest(self):
      return self.manifest_dir / self.hfs_vers 

    #############################

  def env_init(self):
    if self.hfs_path.exists():
      log.marker("registering Houdini SDK @ %s" % self.hfs_path)
      env.set("HFS",self.hfs_path)
      env.append("PATH",self.hfs_path/"bin")
