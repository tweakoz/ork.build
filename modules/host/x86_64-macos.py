###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, multiprocessing
from ork import target

class hostinfo:
  ###################################
  def __init__(self):
    self.architecture = "x86_64"
    self.os = "macos"
    self.distribution = "macos"
    revision = platform.mac_ver()[0]
    self.revision = revision
    ###################################
    self.codename = "mojave"
    sliced = int(revision[0:2])
    if(sliced==11):
      self.codename = "bigsur"
    if(sliced==12):
      self.codename = "monterey"
    if(sliced==13):
      self.codename = "ventura"
    ###################################
    x86_64_macos = target.descriptor('x86_64','macos')
    aarch64_macos = target.descriptor('aarch64','macos')
    aarch64_ios = target.descriptor('aarch64','ios')
    aarch64_android = target.descriptor('aarch64','android')
    targets = set()
    targets.add(x86_64_macos)
    targets.add(aarch64_macos)
    targets.add(aarch64_ios)
    targets.add(aarch64_android)
    self.targets = targets
    self.target = x86_64_macos # host SDK
    ###################################
  ###################################
  def env_init(self):
    print("MACOS-X86_64 Host Activated...")
  ###################################
  @property
  def num_cores(self):
    return multiprocessing.cpu_count()
  ###################################
  @property
  def identifier(self):
    return "x86_64-linux"
    
