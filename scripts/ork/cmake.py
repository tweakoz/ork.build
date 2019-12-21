###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork.command import Command
from ork import path, dep

class context:

  def __init__(self,root="",env=dict()):
    dep.require("cmake")
    self.root = root
    self.env = env

  def exec(self):

    cmdlist = ["cmake"]
    cmdlist += ["-DCMAKE_INSTALL_PREFIX=%s"%path.prefix()]
    for k in self.env.keys():
      v = self.env[k]
      print(k,v)
      value = "-D%s"%str(k)
      if isinstance(v,type(None)):
        pass
      if isinstance(v,bool):
        value += '=ON' if v else '=OFF'
      else:
        value += "="+str(v)
      cmdlist += [value]

    cmdlist += [str(self.root)]

    return Command(cmdlist).exec()
    pass
