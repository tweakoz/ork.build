###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform
SYSTEM = platform.system()
print("SYSTEM<%s>" % SYSTEM)

IsOsx = (SYSTEM=="Darwin")
IsIrix = (SYSTEM=="IRIX64") 
IsLinux = (SYSTEM=="Linux")
IsIx = IsLinux or IsOsx or IsIrix

###############################################################################

from ork.deco import Deco

adeco = Deco()

print("host.IsLinux<%s>" % adeco.val(IsLinux))
print("host.IsIrix<%s>" % adeco.val(IsIrix))
print("host.IsOsx<%s>" % adeco.val(IsOsx))
print("host.IsIx<%s>" % adeco.val(IsIx))
