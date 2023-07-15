###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import obt.xcode 

class sdkinfo:
  def __init__(self):
    self.identifier = "x86_64-linux"
    self.architecture = "x86_64"
    self.os = "linux"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["x86_64-linux"]

