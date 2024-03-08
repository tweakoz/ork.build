from obt._dep_build import BaseBuilder
from obt._dep_impl import require
from obt import pathtools, path, _globals
from obt import make
from obt.command import Command
import obt.host
from collections.abc import Callable

###############################################################################

class AutoConfBuilder(BaseBuilder):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    ##################################
    self._needaclocal = False
    self._needsautogendotsh = False
    self._parallelism=1.0
    self._options = list()
    self._envvars = dict()
    if _globals.tryBoolOption("serial"):
      self._parallelism=0.0
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setEnvVar(self,key,value):
    self._envvars[key] = value
  ###########################################
  def setConfVar(self,key,value):
    self._confvar[key] = value
  ###########################################
  def setOption(self,opt):
    self._options += [opt]
  ###########################################
  def setConfVars(self,othdict):
    for k in othdict:
      self._confvar[k] = othdict[k]
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    ok2build = require(self._deps)
    if not ok2build:
      return False
    retc = 0
    pathtools.mkdir(blddir)
    if incremental:
      os.chdir(blddir)
    else:

      if self._needaclocal:
        pathtools.chdir(srcdir)
        retc = Command(["aclocal"]).exec()
        if retc!=0:
          print(deco.red("Error running aclocal<%d>"%retc))
          return False
      if self._needsautogendotsh:
        pathtools.chdir(srcdir)
        retc = Command(["./autogen.sh"]).exec()
        if retc == 0:
           make.exec("distclean")
        else:
          print(deco.red("Error running autogen.sh<%d>"%retc))
          return False

      pathtools.mkdir(blddir,clean=True)
      pathtools.chdir(blddir)

      retc = Command([srcdir/"configure",
                      '--prefix=%s'%path.prefix()
                     ]+self._options,
                     environment=self._envvars
                     ).exec()
      if retc==0:
        make.exec("all")
        retc = make.exec("install",parallelism=0.0)
    print("retc<%d>"%int(retc))
    return retc==0
  ###########################################
  def install(self,blddir):
    pathtools.chdir(blddir)
    return (make.exec("install",parallelism=0.0)==0)
  ###########################################

