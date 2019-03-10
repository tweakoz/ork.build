###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform
import multiprocessing
SYSTEM = platform.system()
IsOsx = (SYSTEM=="Darwin")
IsIrix = (SYSTEM=="IRIX64") 
IsLinux = (SYSTEM=="Linux")
IsIx = IsLinux or IsOsx or IsIrix
NumCores = multiprocessing.cpu_count()