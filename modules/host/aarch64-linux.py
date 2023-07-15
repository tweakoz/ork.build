###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, multiprocessing 
from obt import target, osrelease

class hostinfo:
  def __init__(self):
    self.architecture = "aarch64"
    self.os = "linux"
    host_info = osrelease.descriptor()
    self.distribution = host_info.id
    self.revision = host_info.version_id
    self.codename = host_info.version_codename
    ###################################
    aarch64_linux = target.descriptor('aarch64','linux')
    targets = set()
    targets.add(aarch64_linux)
    self.targets = targets
    self.target = aarch64_linux # host SDK
    ###################################

  @property
  def is_debian(self):
    apt_exists = os.path.exists("/etc/apt")
    return apt_exists
  @property
  def num_cores(self):
    return multiprocessing.cpu_count()
  @property
  def identifier(self):
    return "aarch64-linux"
