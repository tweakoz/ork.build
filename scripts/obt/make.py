###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt.command import Command
import obt.host
import obt.math

def exec(target=None,parallelism=1.0):
  """
  Execute make with target and specific parallelism.
   Assumes Makefile present in current directory.
  Keyword Arguments:
  target - makefile target (eg all, default, install, etc..)
  parallelism - numjobs normalized to numcores/2 (0.0: numjobs=1, 1.0: numjobs=numcores/2)
  """
  cmd = ["make"]
  print("make with parallel<%g>"%parallelism)
  if parallelism!=0.0:
    p = obt.math.clamp(parallelism,0.0,1.0)
    numcores = int(obt.host.NumCores*p)
    numcores = obt.math.clamp(numcores,1,obt.host.NumCores)
    cmd += ["-j",numcores]
  if target!=None:
    cmd += [target]
  return Command(cmd).exec()
