###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import ork.dep

dep_boost = ork.dep.require("boost")
#

class wt(ork.dep.Provider):

	def __init__(self,options=None):
		parclass = super(wt,self)
		parclass.__init__(options=options)
		print(options)
		pass

	def provide(self):
		return None
