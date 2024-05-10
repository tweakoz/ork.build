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
    self.architecture = "x86_64"
    self.os = "linux"
    descriptor = osrelease.descriptor()
    self.distribution = descriptor.id
    self.revision = descriptor.version_id
    self.codename = descriptor.version_codename
    self.id = "x86_64"
    ###################################
    x86_64_linux = target.descriptor('x86_64','linux')
    aarch64_android = target.descriptor('aarch64','android')
    targets = set()
    targets.add(x86_64_linux)
    targets.add(aarch64_android)
    self.targets = targets
    self.target = x86_64_linux # host SDK
    ###################################

  @property
  def is_gentoo(self):
    portage_exists = os.path.exists("/etc/portage")
    return portage_exists
  @property
  def is_debian(self):
    apt_exists = os.path.exists("/etc/apt")
    return apt_exists
  @property
  def num_cores(self):
    return multiprocessing.cpu_count()
  @property
  def identifier(self):
    return "x86_64-linux"
