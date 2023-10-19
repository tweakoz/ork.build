#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

###########################################

import pathlib, os, sys

###########################################
# setup sys.path so we can import _obt_config
###########################################

Path = pathlib.Path
curwd = Path(os.getcwd())
file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
sys.path.append(str(file_dir))

###########################################
# minimal OBT support for non-environment shell
###########################################

from _obt_config import configFromCommandLine
obt_config = configFromCommandLine()
from obt import path, pathtools, env, command

###########################################


