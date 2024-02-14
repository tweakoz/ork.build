from yarl import URL
from obt import dep, path, pathtools, command

###############################################################################

class dsp(dep.StdProvider):
  VERSION = "v1.5.0"
  name = "dsp"
  def __init__(self):
    build_dir = path.builds()/dsp.name
    super().__init__(dsp.name)
    
    pathtools.ensureDirectoryExists(path.includes()/"dsp")

    items = pathtools.patglob(self.source_root, "*.h")
    print(items)

    copy_commands = []
    for item in items:
      print(item)
      cmd = command.Command([
        "cp",str(item), str(path.includes()/"dsp")+"/"
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
    return dep.GithubFetcher(name=dsp.name,
                             repospec="Signalsmith-Audio/dsp",
                             revision=dsp.VERSION,
                             recursive=False)

  #######################################################################

  def areRequiredSourceFilesPresent(self):
    print(self.source_root)
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"dsp"/"fft.h").exists()
