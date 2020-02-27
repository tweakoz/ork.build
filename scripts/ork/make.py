###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork.command import Command
import ork.host
import ork.math

def exec(target=None,parallelism=1.0):
  """
  Execute make with target and specific parallelism.
   Assumes Makefile present in current directory.
  Keyword Arguments:
  target - makefile target (eg all, default, install, etc..)
  parallelism - numjobs normalized to numcores/2 (0.0: numjobs=1, 1.0: numjobs=numcores/2)
  """
  cmd = ["make"]
  if parallelism!=0.0:
    p = ork.math.clamp(parallelism,0.0,1.0)
    numcores = int(ork.host.NumCores*p*0.5)
    numcores = ork.math.clamp(numcores,1,ork.host.NumCores)
    cmd += ["-j",numcores]
  if target!=None:
    cmd += [target]
  return Command(cmd).exec()
