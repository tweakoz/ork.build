from obt._dep_build import BaseBuilder
from obt._dep_impl import require
from obt import pathtools, path, _globals
from obt import command 
from collections.abc import Callable
import os

###############################################################################

class ConanBuilder(BaseBuilder):
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
    self._environment = dict()
    self._cmdlist = []
    self._cmdlist2 = []
    self._working_dir = None
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
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    os.chdir(str(self._working_dir))
    retval = command.run(self._cmdlist, #
                         environment=self._environment,do_log=True )
    if retval==0:
      retval = command.run(self._cmdlist2, #
                           environment=self._environment,do_log=True )
    return retval==0
  ###########################################
  def install(self,blddir):
    return True
  ###########################################
