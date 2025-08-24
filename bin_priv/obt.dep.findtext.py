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
import obt.path
import obt.dep
import obt.search_args

args, ext_set = obt.search_args.parse_search_args(
    description='Search text in a specific dependency',
    require_dep=True
)
_args = vars(args)

#################################################################################

if _args["dep"]!=None:
  depname = _args["dep"]
  path_list = [obt.path.builds()/depname]
  ########################
  depnode = obt.dep.DepNode.FIND(depname)
  depinst = depnode.instance
  ########################
  # allow dep module to override default search path
  ########################
  if hasattr(depinst,"find_paths"):
    path_list = depinst.find_paths()
  ########################
  words = _args["keywords"]
  rem_root = path_list[0]
  
  # Pass all search options to execute_at
  obt.search.execute_at(words, path_list, 
                       remove_root=rem_root, 
                       ext_set=ext_set,
                       case_insensitive=args.case_insensitive,
                       regex=args.regex,
                       whole_word=args.whole_word,
                       invert_match=args.invert_match,
                       files_only=args.files_only,
                       before_context=args.before_context,
                       after_context=args.after_context)
