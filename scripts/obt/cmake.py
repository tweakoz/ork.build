###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt.command import Command
from obt import path, dep, buildtrace
import os 

class context:

  ###############################################

  def __init__(self,
               root="",
               env=dict(),
               osenv=dict(),
               trace=False,
               sourcedir=None,
               builddir=None,
               working_dir=None,
               xcode=False,
               install_prefix=None):

    self.root = root
    self.env = env
    self.osenv = osenv
    self._verbose = False
    self._trace = trace
    self._builddir = builddir 
    self._working_dir = working_dir
    self._sourcedir = sourcedir
    self._xcode = xcode
    self._install_prefix = install_prefix

    if builddir!=None:
      self._sourcedir = builddir/".."
    if sourcedir!=None:
      self._sourcedir = sourcedir

  ###############################################

  @property 
  def install_prefix(self):
    return path.prefix() if (self._install_prefix==None) else self._install_prefix

  ###############################################

  def verbose(self,enable):
    self._verbose = enable

  ###############################################

  def exec(self):

    cmdlist = ["cmake"]

    if self._builddir!=None:
      cmdlist += [ "-B", self._builddir ]

    cmdlist += [ "-S", self._sourcedir ]

    if self._verbose:
      cmdlist += ["--verbose"]

    cmdlist += ["-DCMAKE_INSTALL_PREFIX=%s"%self.install_prefix]
    cmdlist += ["-DCMAKE_MODULE_PATH=%s"%(self.install_prefix/"lib"/"cmake")]

    proc_env = dict()

    for k in self.env.keys():
      v = self.env[k]
      print(k,v)
      value = "-D%s"%str(k)
      pe_val = "DEFINED"
      if isinstance(v,type(None)):
        pass
      if isinstance(v,bool):
        value += '=ON' if v else '=OFF'
        pe_val = 'ON' if v else 'OFF'
      else:
        value += "="+str(v)
        pe_val = str(v)
      proc_env[k] = pe_val
      cmdlist += [value]

    if self._trace:
      cmdlist += ["--trace"]

    if self._builddir==None:
      cmdlist += [str(self.root)]

    if self._xcode:
      cmdlist += ["-G","Xcode"]

    the_env = dict(os.environ)
    for k in self.osenv.keys():
      the_env[k] = str(self.osenv[k])
    #the_env["XXX"] = "xxx"

    with buildtrace.NestedBuildTrace({  
     "op": "cmake",
     "source_dir": self.root, 
     "build_dir": self._builddir,
     "prefix": self.install_prefix, 
     "module_path": self.install_prefix/"lib"/"cmake",
     "cmake_env": proc_env,
     "os_env": the_env }) as nested:
       return Command(cmdlist,environment=the_env,working_dir=self._working_dir).exec()
