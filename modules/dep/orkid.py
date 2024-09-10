###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, pathtools, log, env, command, host
import os
###############################################################################
class orkid(dep.StdProvider):
  name = "orkid"

  def __init__(self):
    super().__init__(orkid.name,subspace_vif=2)
    self.scope = dep.ProviderScope.SUBSPACE    
    self._oslist = ["Linux","Darwin"]
    self._archlist = ["x86_64","aarch64"]
    self._allow_build_in_subspaces = True 
    self._userworkingcopy = False    
    
    ################################
    # default orkid_src_dir is in builds/orkid (from dep fetcher)
    ################################

    self.orkid_src_dir = path.builds()/"orkid"

    ################################
    # if ORKID_IS_MAIN_PROJECT set,
    #  use that as orkid_src_dir
    ################################

    x = None

    if "OBT_PROJECT_DIRS" in os.environ:
      for dir in os.environ["OBT_PROJECT_DIRS"].split(":"):
        if (path.Path(dir)/"orkid.cmake").exists():
          x = path.Path(dir)
          self._userworkingcopy = (x/"orkid.cmake").exists()
          break
      
    if self._userworkingcopy:
      self.orkid_src_dir = x
      assert(self.orkid_src_dir==x)
      self.source_root = x
      self.build_src = x

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

  ########################################################################
  @property
  def github_repo(self):
    return "tweakoz/orkid"
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
                               repospec=self.github_repo,
                               revision=self.revision,
                               recursive=True,
                               shallow=False)

  ########

  @property
  def _envinitcommands(self):
    return ["obt.env.launch.py",
      "--stack", path.stage(),
      "--novars", # use parent environment variables
      "--project", path.builds()/"orkid",
    ]

  ########

  @property
  def _inner_build_command(self):
    ork_build_script = self.orkid_src_dir/"obt.project"/"bin"/"ork.build.py"
    inner_build_command = [str(ork_build_script), "--builddir", str(self.builddir)]
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
    deplist += ["igl"]
    deplist += ["dsp"]
    deplist += ["dspstretch"]
    #deplist += ["libsurvive"]

    if host.IsX86_64:
      deplist += ["openvdb"]

    #if ork.host.IsOsx: # until moltenvk fixed on big sur
    #   ork.dep.require(["moltenvk"])
    
    if host.IsLinux:
      deplist += ["vulkan"]
      deplist += ["rtmidi"]
      #deplist += ["pipewire"]
      if host.IsX86_64:
        deplist += ["openvr"]
        deplist += ["ispctexc"]
        #deplist += ["nvtt"]
    elif host.IsDarwin:
      deplist += ["moltenvk"]
      deplist += ["audiofile"]

    return deplist

  ########
  def update(self):
    self.builddir.chdir()
    self._fetcher.update()

  ########
  def on_build_shell(self):
    shell_cmd = command.Command([
      "obt.env.launch.py",
      "--stack", path.stage(),
      "--project", path.builds()/"orkid",
      "--chdir", path.builds()/"orkid"
    ])
    return shell_cmd.exec()

  ########

  def env_init(self):
    log.marker("registering Orkid(%s) SDK @ %s"%(self.revision,self.orkid_src_dir))
    env.set("ORKID_WORKSPACE_DIR",self.orkid_src_dir)
    env.set("ORKID_LEV2_EXAMPLES_DIR",self.orkid_src_dir/"ork.lev2"/"examples")
    env.append("PATH",self.orkid_src_dir/"obt.project"/"bin")

  ########

  def env_goto(self):
    return { "orkid": self.orkid_src_dir }
    
  ########
  def find_paths(self):
    return [self.source_root/"ork.core",self.source_root/"ork.lev2",self.source_root/"ork.ecs"]

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"orkid.cmake").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/("libork_core.%s"%self.shlib_extension)).exists()
