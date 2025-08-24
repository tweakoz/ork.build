#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string
import obt.search
import obt.search_args

#################################################################################

if __name__ == "__main__":
 args, ext_set = obt.search_args.parse_search_args(
     description='Search text in all OBT projects',
     require_dep=False
 )
 
 # execute expects a single word, not a list
 for word in args.keywords:
     obt.search.execute(word, ext_set=ext_set)
