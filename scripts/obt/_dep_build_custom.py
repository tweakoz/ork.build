from obt._dep_build import BaseBuilder
from obt._dep_impl import require
from obt import pathtools, path, _globals
from obt.command import Command
from collections.abc import Callable

###############################################################################

class CustomStep:
  def __init__(self,name,funktor):
    super().__init__()
    self._name = name
    self._funktor = funktor 

###############################################################################

class CustomBuilder(BaseBuilder):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    ##################################
    self._envvars = dict()
    self._parallelism=1.0
    self._cleanbuildcommands = list()
    self._incrbuildcommands = list()
    self._installcommands = list()
    self._builddir = path.builds()/name
    self._invokeBeforeBuild = None

    if _globals.tryBoolOption("serial"):
      self._parallelism=0.0
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setEnvVar(self,key,value):
    self._envvars[key] = value
  ###########################################
  def setEnvVars(self,othdict):
    for k in othdict:
      self._envvars[k] = othdict[k]
  ###########################################
  def _run_commands(self,cmdlist):
    if len(cmdlist)>0:
      for cmd in cmdlist:
        if isinstance(cmd,Command):
          retc = cmd.exec()
          if retc!=0:
            return False
        elif isinstance(cmd,CustomStep):
          retc = cmd._funktor()
          if retc==False:
            return False
        elif isinstance(cmd,Callable):
          if cmd()==False:
            return False
    return True
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    
    if(self._invokeBeforeBuild!=None):
      self._invokeBeforeBuild()
      
    print("srcdir<%s>"%srcdir)
    print("blddir<%s>"%blddir)
    print("incremental<%s>"%incremental)
    print("deps<%s>"%self._deps)
    ok2build = require(self._deps)
    print("ok2build<%d>"%int(ok2build))
    if not ok2build:
      return False
    ###################################
    if incremental:
    ###################################
      print("doing incremental build...")
      print(self._incrbuildcommands)
      pathtools.mkdir(self._builddir,clean=False,parents=True)
      pathtools.chdir(self._builddir)
      return self._run_commands(self._incrbuildcommands)
    ###################################
    else: # clean build
    ###################################
      print("doing clean build...")
      print(self._cleanbuildcommands)
      pathtools.mkdir(self._builddir,clean=False,parents=True)
      pathtools.chdir(self._builddir)
      return self._run_commands(self._cleanbuildcommands)
  ###########################################
  def install(self,blddir):
    pathtools.chdir(self._builddir)
    return self._run_commands(self._installcommands)
  ###########################################
