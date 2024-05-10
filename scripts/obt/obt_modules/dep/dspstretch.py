from yarl import URL
from obt import dep, path, pathtools, command

###############################################################################

class dspstretch(dep.StdProvider):
  VERSION = "c315378"
  name = "dspstretch"
  def __init__(self):
    build_dir = path.builds()/dspstretch.name
    super().__init__(dspstretch.name)
    
    self.dest_header_path = path.includes()/"dspstretch"
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False

    def before_build():
      print("before_build")
      pathtools.ensureDirectoryExists(self.dest_header_path)
      items = pathtools.patglob(self.source_root, "*.h")
      copy_commands = []
      for item in items:
        print(item)
        cmd = command.Command([
          "cp",str(item), str(self.dest_header_path)+"/"
          ])
        copy_commands.append(cmd)
      self._builder._cleanbuildcommands = copy_commands
      self._builder._incrbuildcommands = copy_commands
      print("copy_commands: %s" % copy_commands)
    
    self._builder._invokeBeforeBuild = before_build

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=dspstretch.name,
                             repospec="Signalsmith-Audio/signalsmith-stretch",
                             revision=dspstretch.VERSION,
                             recursive=True)

  #######################################################################

  def areRequiredSourceFilesPresent(self):
    print(self.source_root)
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"dspstretch"/"signalsmith-stretch.h").exists()
