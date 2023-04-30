###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path, pathtools, log, env, command, host
import os
###############################################################################
class orkid(dep.StdProvider):
  name = "orkid"

  def __init__(self):
    super().__init__(orkid.name)
    self._oslist = ["Linux","Darwin"]
    self._archlist = ["x86_64","aarch64"]
    self.setAllowedSubspaces(["*"])
    ################################
    # default orkid_src_dir is in builds/orkid (from dep fetcher)
    ################################

    self.orkid_src_dir = path.builds()/"orkid"

    ################################
    # if ORKID_IS_MAIN_PROJECT set,
    #  use that as orkid_src_dir
    ################################

    self._userworkingcopy = ("ORKID_IS_MAIN_PROJECT" in os.environ)
    if self._userworkingcopy:
      self.orkid_src_dir = path.Path(os.environ["ORKID_WORKSPACE_DIR"])
      self.overrideSourceRoot(path.Path(os.environ["ORKID_WORKSPACE_DIR"]))

    ################################

    for item in self.deplist:
      self.declareDep(item)

    ################################

    self._builder = dep.CustomBuilder(orkid.name)

    self.builddir = path.subspace_python_build_dir/"orkid"/".build"
    self._builder._builddir = self.builddir

    ###########################################################

    self._builder._cleanbuildcommands += [self._outer_build_command]
    self._builder._incrbuildcommands += [self._outer_build_command]

  ########

  @property
  def revision(self):
    return "develop"

  @property
  def _fetcher(self):
    if self._userworkingcopy:
      pathtools.mkdir(self.builddir,parents=True)
      return dep.NopFetcher(name=orkid.name)
    else:
      return dep.GithubFetcher(name=orkid.name,
                               repospec="tweakoz/orkid",
                               revision=self.revision,
                               recursive=True,
                               shallow=False)

  ########

  @property
  def _envinitcommands(self):
    return [path.obt_bin()/"init_env.py",
      "--stack", path.stage(),
      "--novars", # use parent environment variables
      "--compose", path.builds()/"orkid",
    ]

  ########

  @property
  def _inner_build_command(self):
    inner_build_command = ["ork.build.py", "--builddir", str(self.builddir)]
    if dep._globals.getOption("debug"):
      inner_build_command += ["--debug"]
    if dep._globals.getOption("verbose"):
      inner_build_command += ["--verbose"]
    if dep._globals.getOption("serial"):
      inner_build_command += ["--serial"]
    #inner_build_command += ["--trace"]
    return inner_build_command

  ########

  @property
  def _outer_build_command(self):
    return command.Command(self._envinitcommands +
                           ["--command", " ".join(self._inner_build_command)])

  ########

  @property
  def deplist(self):
    deplist = []

    deplist += ["cmake"]
    deplist += ["pydefaults"]
    deplist += ["python"]
    deplist += ["pybind11"]
    deplist += ["openexr"]
    deplist += ["oiio"]
    deplist += ["assimp"]
    deplist += ["rapidjson"]
    deplist += ["luajit"]
    deplist += ["glfw"]
    deplist += ["lexertl14"]
    deplist += ["parsertl14"]
    deplist += ["easyprof"]
    deplist += ["eigen"]
    deplist += ["glm"]
    deplist += ["bullet"]
    deplist += ["rtmidi"]
    deplist += ["zmq"]
    deplist += ["cppzmq"]
    deplist += ["cpppeglib"]
    deplist += ["klein"]
    deplist += ["portaudio"]
    deplist += ["sigslot"]
    deplist += ["openblas"]

    if host.IsX86_64:
      deplist += ["ispctexc"]
      deplist += ["openvdb"]

    #if ork.host.IsOsx: # until moltenvk fixed on big sur
    #   ork.dep.require(["moltenvk"])
    
    if host.IsLinux:
      deplist += ["igl"]
      deplist += ["vulkan"]
      deplist += ["rtmidi"]
      if host.IsX86_64:
        deplist += ["openvr"]
        deplist += ["nvtt"]

    return deplist

  ########
  def update(self):
    self.builddir.chdir()
    self._fetcher.update()

  ########
  def on_build_shell(self):
    shell_cmd = command.Command([
      path.obt_bin()/"init_env.py",
      "--stack", path.stage(),
      "--compose", path.builds()/"orkid",
      "--chdir", path.builds()/"orkid"
    ])
    return shell_cmd.exec()
  ########
  def env_init(self):
    log.marker("registering Orkid(%s) SDK"%self.revision)
    env.set("ORKID_WORKSPACE_DIR",self.orkid_src_dir)
  ########
  def find_paths(self):
    return [self.source_root/"ork.core",self.source_root/"ork.lev2"]

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"orkid.cmake").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libork_core.so").exists()
