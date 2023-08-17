#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string
from obt.path import Path as path
from obt.deco import Deco

deco = Deco()

#################################################################################

def display_var(name):
    print( "%s : %s" % (deco.key(name), deco.val(os.environ[name])) )

def display_path_var(name):
    p = path(os.environ[name]).norm
    print( "%s : %s" % (deco.key(name), deco.val(str(p))) )

#################################################################################

display_path_var("OBT_STAGE")
display_path_var("OBT_ROOT")
display_path_var("OBT_BUILDS")
display_path_var("OBT_PROJECT_DIR")
display_path_var("OBT_PYTHONHOME")
display_path_var("OBT_MODULES_PATH")
display_path_var("OBT_DEP_PATH")
display_path_var("OBT_SUBSPACE_DIR")
display_var("OBT_SUBSPACE")
