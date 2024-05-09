###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

class targetinfo:
 def __init__(self):
   self.architecture = "aarch64"
   self.os = "macos"
   self.c_compiler = "clang"
   self.cxx_compiler = "clang++"
   self.identifier = "aarch64-macos"