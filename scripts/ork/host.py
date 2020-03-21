###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, os
import multiprocessing
SYSTEM = platform.system()
IsOsx = (SYSTEM=="Darwin")
IsIrix = (SYSTEM=="IRIX64")
IsLinux = (SYSTEM=="Linux")
IsIx = IsLinux or IsOsx or IsIrix

if "OBT_NUM_CORES" in os.environ:
  NumCores = int(os.environ["OBT_NUM_CORES"])
else:
  NumCores = multiprocessing.cpu_count()

if IsLinux:
    PlatformId = "ix"
elif IsOsx:
    PlatformId = "osx"
else:
    PlatformId = "unknown"
