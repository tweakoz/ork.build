VERSION = "19.0"

from ork import dep, host, path, git, pathtools, command, patch, env
from ork import log

class houdini(dep.Provider):
  def __init__(self): ############################################
    super().__init__("houdini")
    self.enabled = False
    #print(options)
    self.hfs_vers = "hfs%s"%VERSION
    self.hfs_path = path.Path("/opt")/self.hfs_vers
    #assert(False)
    #self.source_root = path.builds()/"houdini"
    #self.build_dest = self.source_root
    #self.header_dest = path.prefix()/"include"/"houdini"
    #self.OK = True

  def env_init(self):
    if self.hfs_path.exists():
      log.marker("registering Houdini SDK @ %s" % self.hfs_path)
      env.set("HFS",self.hfs_path)
      env.append("PATH",self.hfs_path/"bin")
