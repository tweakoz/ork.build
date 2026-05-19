###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt.command import Command
import obt.host
from obt import obt_math

def exec(target=None,parallelism=1.0,working_dir=None):
  """
  Execute make with target and specific parallelism.
  Keyword Arguments:
  target      - makefile target (eg all, default, install, etc..)
  parallelism - numjobs normalized to numcores/2 (0.0: numjobs=1, 1.0: numjobs=numcores/2)
  working_dir - directory containing the Makefile. If None, runs in the
                parent process's cwd — UNSAFE under the parallel pipeline
                because concurrent workers race on cwd. Callers in the
                pipeline MUST pass an explicit working_dir.
  """
  cmd = ["make"]
  print("make with parallel<%g>"%parallelism)
  if parallelism!=0.0:
    p = obt_math.clamp(parallelism,0.0,1.0)
    numcores = int(obt.host.NumCores*p)
    numcores = obt_math.clamp(numcores,1,obt.host.NumCores)
    cmd += ["-j",numcores]
  if target!=None:
    cmd += [target]
  return Command(cmd,working_dir=working_dir).exec()
