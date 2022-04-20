###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork.command import Command
from ork import path, dep, buildtrace
import os 
class context:

  def __init__(self,root="",env=dict(),trace=False,builddir=None):
    self.root = root
    self.env = env
    self._verbose = False
    self._trace = trace
    self._builddir = builddir 

  def verbose(self,enable):
    self._verbose = enable

  def exec(self):

    cmdlist = ["cmake"]

    if self._builddir!=None:
      cmdlist += [ "-B", self._builddir ]

    if self._verbose:
      cmdlist += ["--verbose"]

    cmdlist += ["-DCMAKE_INSTALL_PREFIX=%s"%path.prefix()]
    cmdlist += ["-DCMAKE_MODULE_PATH=%s"%(path.libs()/"cmake")]

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

    cmdlist += [str(self.root)]

    the_env = dict(os.environ)
    #the_env["XXX"] = "xxx"

    with buildtrace.NestedBuildTrace({  
     "op": "cmake",
     "source_dir": self.root, 
     "build_dir": self._builddir,
     "prefix": path.prefix(), 
     "module_path": path.libs()/"cmake",
     "cmake_env": proc_env,
     "os_env": the_env }) as nested:
       return Command(cmdlist,environment=the_env).exec()
