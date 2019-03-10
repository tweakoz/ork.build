###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork.command import Command
import ork.host

def exec(target=None,parallel=True):
	cmd = ["make"]
	if parallel:
		cmd += ["-j",ork.host.NumCores]
	if target!=None:
		cmd += [target]
	Command(cmd).exec()