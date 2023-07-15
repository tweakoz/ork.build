###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, host

###############################################################################

class root(dep.Provider): # dummy dep for including pydefaults for everyone
  def __init__(self):
    name = "root"
    super().__init__(name)
    self.declareDep("pydefaults")
  ########################################################################
  def build(self):
    return True
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return True
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return True
