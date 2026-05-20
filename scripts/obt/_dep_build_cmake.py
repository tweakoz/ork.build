import os 
from obt._dep_build import BaseBuilder
from obt._dep_impl import require
from obt import pathtools, path, _globals
from obt import cmake, make
from obt.command import Command
import obt.host
from collections.abc import Callable

###############################################################################

class CMakeBuilder(BaseBuilder):
  ###########################################
  def __init__(self,
               name,
               static_libs=False,
               macos_defaults=True,
               install_prefix=None,
               src_dir_override=None,
               modules_paths=[],
               os_env=dict()):
    super().__init__(name)
    self._minimal = False 
    self._install_prefix = install_prefix
    self._src_dir_override = src_dir_override
    self._modules_paths = modules_paths
    self._os_env = os_env
    ##################################
    # ensure environment cmake present
    ##################################
    self._cmakeenv = {
      "CMAKE_BUILD_TYPE": "Release",
    }
    self._osenv = {
    }

    if not static_libs:
      self._cmakeenv["BUILD_SHARED_LIBS"]="ON"

    ##################################
    # default OSX stuff
    ##################################
    if obt.host.IsOsx and macos_defaults:
      sysroot_cmd = Command(["xcrun","--show-sdk-path"],do_log=False)
      sysroot = sysroot_cmd.capture().replace("\n","")

      if obt.host.IsAARCH64:
        self._cmakeenv.update({"CMAKE_HOST_SYSTEM_PROCESSOR":"arm64"})
      else:
        self._cmakeenv.update({"CMAKE_HOST_SYSTEM_PROCESSOR":"x86_64"})

      self._cmakeenv.update({
        "CMAKE_OSX_DEPLOYMENT_TARGET:STRING":"11",
        "CMAKE_OSX_SYSROOT:STRING":sysroot,
        "CMAKE_MACOSX_RPATH": "1",
        "CMAKE_INSTALL_RPATH": path.libs(),
        "CMAKE_SKIP_INSTALL_RPATH:BOOL":"NO",
        "CMAKE_SKIP_RPATH:BOOL":"NO",
        "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib"
      })

    ##################################
    self._parallelism = 0.0 if _globals.tryBoolOption("serial") else 1.0
    ##################################
    # implicit dependencies
    ##################################
    if name!="cmake":
      self._deps += ["cmake"]
  ###############################################
  @property 
  def install_prefix(self):
    return path.prefix() if (self._install_prefix==None) else self._install_prefix
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setCmVar(self,key,value):
    self._cmakeenv[key] = value
  ###########################################
  def setCmVars(self,othdict):
    for k in othdict:
      self._cmakeenv[k] = othdict[k]
  ###########################################
  def useMold(self):
    """Route this dep's link steps through the mold linker (Linux only).

    mold sharply cuts the link phase of large C++ projects. Per-dep opt-in:
    a dep calls this in __init__ after createBuilder(). No-op on non-Linux —
    mold is ELF-only and macOS's linker is already fast. Requires the host
    `mold` package (see obt.ix.installdeps.ubuntu_x86_64.py). Appends to any
    linker flags the dep already set rather than clobbering them."""
    if not obt.host.IsLinux:
      return self
    flag = "-fuse-ld=mold"
    for k in ("CMAKE_EXE_LINKER_FLAGS",
              "CMAKE_SHARED_LINKER_FLAGS",
              "CMAKE_MODULE_LINKER_FLAGS"):
      existing = self._cmakeenv.get(k, "")
      self._cmakeenv[k] = (existing + " " + flag).strip()
    return self
  ###########################################
  @property 
  def cmakeEnvAsString(self):
    return " ".join(self.cmakeEnvAsStringList)
  ###########################################
  @property 
  def cmakeEnvAsStringList(self):
    args = []
    for k in self._cmakeenv:
      v = self._cmakeenv[k]
      args += ["-D%s=%s"%(k,v)]
    return args
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    print("srcdir<%s>"%srcdir)
    print("blddir<%s>"%blddir)
    print("wrkdir<%s>"%wrkdir)
    print("srcovr<%s>"%self._src_dir_override)

    ok2build = require(self._deps)
    if not ok2build:
      return False

    environ_cached = os.environ.copy()

    os.environ.update(self._os_env)
    
    # NOTE: we used to pathtools.chdir(wrkdir) here before invoking cmake/make.
    # That's a process-global mutation, so two parallel workers would clobber
    # each other's cwd and cause "make: *** No rule to make target install"
    # / "Cannot build <X> missing files" failures. cmake.context and make.exec
    # both accept a working_dir / builddir param now; pass it through.
    if incremental:
      pathtools.mkdir(blddir,clean=False)
      cmake_ctx = cmake.context(root=srcdir,
                                env=self._cmakeenv,
                                osenv=self._osenv,
                                builddir=blddir,
                                working_dir=wrkdir,
                                sourcedir=self._src_dir_override,
                                install_prefix=self.install_prefix,
                                modules_paths = self._modules_paths)
      ok2build = cmake_ctx.exec()==0
    else:
      pathtools.mkdir(blddir,clean=True,parents=True)
      cmake_ctx = cmake.context(root=srcdir,
                                env=self._cmakeenv,
                                builddir=blddir,
                                working_dir=wrkdir,
                                sourcedir=self._src_dir_override,
                                osenv=self._osenv)
      ok2build = cmake_ctx.exec()==0

    if ok2build:
      OK = (make.exec(parallelism=self._parallelism,working_dir=blddir)==0)
      if OK and self._onPostBuild!=None:
        self._onPostBuild()
        os.environ = environ_cached
      return OK
    os.environ = environ_cached
    return False
  ###########################################
  def install(self,blddir):
    OK = (make.exec("install",parallelism=0.0,working_dir=blddir)==0)
    if OK and self._onPostInstall!=None:
       self._onPostInstall()
    return OK

  ###########################################
