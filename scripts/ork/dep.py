###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile
from pathlib import Path
import importlib.util
import ork.path, ork.host
from ork.command import Command, run
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git, host, _globals
from ork._dep_fetch import *
from ork._dep_build import *
from ork._dep_provider import *
from ork._dep_impl import *
from ork._dep_node import *
from ork._dep_dl import *
from ork._dep_x import *
from ork._dep_enumerate import *
