###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import ork.dep

class boost(ork.dep.Provider):

	def __init__(self,options=None):
		parclass = super(boost,self)
		parclass.__init__(options=options)
		pass

	def provide(self):
		return None
