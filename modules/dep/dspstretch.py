from yarl import URL
from obt import dep, path, pathtools, command

###############################################################################

class dspstretch(dep.StdProvider):
  VERSION = "main"
  name = "dspstretch"
  def __init__(self):
    build_dir = path.builds()/dspstretch.name
    super().__init__(dspstretch.name)
    
    pathtools.ensureDirectoryExists(path.includes()/"dspstretch")

    items = pathtools.patglob(self.source_root, "*.h")
    print(items)

    copy_commands = []
    for item in items:
      print(item)
      cmd = command.Command([
        "cp",str(item), str(path.includes()/"dspstretch")+"/"
        ])
      copy_commands.append(cmd)

    print(copy_commands)
    
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    self._builder._cleanbuildcommands = copy_commands
    self._builder._incrbuildcommands = copy_commands

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
