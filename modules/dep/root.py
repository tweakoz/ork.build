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
    # NOTE: root does NOT declare pybind11. Doing so made pybind11 a
    # universal prereq of everything-via-root, which serialized
    # independent deps (e.g. vulkan) behind pybind11's build. Deps that
    # genuinely use pybind11 declare it themselves; env-create builds it
    # via MANDATORY_DEPS.
  ########################################################################
  def build(self):
    return True
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return True
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return True
