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
               install_prefix=None):
    super().__init__(name)
    self._minimal = False 
    self._install_prefix = install_prefix
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

    ok2build = require(self._deps)
    if not ok2build:
      return False

    if incremental:
      pathtools.mkdir(blddir,clean=False)
      pathtools.chdir(wrkdir)
      cmake_ctx = cmake.context(root=srcdir,
                                env=self._cmakeenv,
                                osenv=self._osenv,
                                builddir=blddir,
                                working_dir=wrkdir,
                                install_prefix=self.install_prefix)
      ok2build = cmake_ctx.exec()==0
    else:
      pathtools.mkdir(blddir,clean=True,parents=True)
      pathtools.chdir(wrkdir)
      cmake_ctx = cmake.context(root=srcdir,
                                env=self._cmakeenv,
                                osenv=self._osenv)
      ok2build = cmake_ctx.exec()==0

    if ok2build:
      OK = (make.exec(parallelism=self._parallelism)==0)
      if OK and self._onPostBuild!=None:
        self._onPostBuild()
      return OK
    return False
  ###########################################
  def install(self,blddir):
    pathtools.chdir(blddir)
    OK = (make.exec("install",parallelism=0.0)==0)
    if OK and self._onPostInstall!=None:
       self._onPostInstall()
    return OK

  ###########################################
