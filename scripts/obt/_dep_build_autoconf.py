from obt._dep_build import BaseBuilder
from obt._dep_impl import require
from obt import pathtools, path, _globals
from obt import make
from obt.command import Command
import obt.host
from collections.abc import Callable

from obt.deco import Deco 
deco = Deco()

###############################################################################

class AutoConfBuilder(BaseBuilder):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    ##################################
    self._needaclocal = False
    self._needsautogendotsh = False
    # When True, run `autoreconf -fi` in srcdir before configure. Use this
    # for sources that ship only configure.ac/Makefile.am with no
    # autogen.sh wrapper (e.g. chirlu/sox-14.4.2).
    self._needsautoreconf = False
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
    # NOTE: removed all pathtools.chdir / os.chdir calls. cwd is process-
    # global; parallel workers would race and one build's make would end
    # up running in another build's directory. Each Command/make call now
    # passes working_dir explicitly so the subprocess's cwd is set via
    # Popen's cwd= rather than mutating the parent process's cwd.
    ok2build = require(self._deps)
    if not ok2build:
      return False
    retc = 0
    pathtools.mkdir(blddir)
    if not incremental:
      if self._needaclocal:
        retc = Command(["aclocal"], working_dir=srcdir).exec()
        if retc!=0:
          print(deco.red("Error running aclocal<%d>"%retc))
          return False
      if self._needsautogendotsh:
        retc = Command(["./autogen.sh"], working_dir=srcdir).exec()
        if retc == 0:
           make.exec("distclean", working_dir=srcdir)
        else:
          print(deco.red("Error running autogen.sh<%d>"%retc))
          return False
      if self._needsautoreconf:
        retc = Command(["autoreconf","-fi"], working_dir=srcdir).exec()
        if retc != 0:
          print(deco.red("Error running autoreconf -fi<%d>"%retc))
          return False

      pathtools.mkdir(blddir,clean=True)

      retc = Command([srcdir/"configure",
                      '--prefix=%s'%path.prefix()
                     ]+self._options,
                     environment=self._envvars,
                     working_dir=blddir,
                     ).exec()
      if retc==0:
        make.exec("all", working_dir=blddir)
        retc = make.exec("install",parallelism=0.0,working_dir=blddir)
    print("retc<%d>"%int(retc))
    return retc==0
  ###########################################
  def install(self,blddir):
    return (make.exec("install",parallelism=0.0,working_dir=blddir)==0)
  ###########################################

