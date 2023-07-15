#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string, argparse
import obt.search
import obt.path
import obt.dep
import obt.deco
deco = obt.deco.Deco()

parser = argparse.ArgumentParser(description='build all box products')
parser.add_argument('--dep', help='dep to search' )
parser.add_argument('--find', help='text to search' )
parser.add_argument('--replace', help='text to replace' )

_args = vars(parser.parse_args())

#################################################################################
find_text = _args["find"]
replace_text = _args["replace"]
assert(type(find_text)==str)
assert(type(replace_text)==str)
#################################################################################
class visitor:
  def __init__(self,find,repl):
    self.by_file = dict()
    self.find = find
    self.repl = repl
  def __del__(self):
    self.process()
#######################
  def onPath(self,pth):
    self._current_root = pth
    print("/////////////////////////////////////////////////////////////")
    print("// replacing! path : %s" % pth)
    print("/////////")
#######################
  def onItem(self,item):
    if item.path not in self.by_file:
      self.by_file[item.path] = list()
    self.by_file[item.path].append(item)
#######################
  def process(self):
    for filename in self.by_file.keys():
      items = self.by_file[filename]
      #print("%s" % (filename))
      if os.path.isfile(filename):
        lines = list()
        with open(filename,"r") as file:
          lines = file.readlines()
          for item in items:
            lineno = item.lineno
            line = lines[lineno-1]
            line = line.replace(self.find,self.repl)
            lines[lineno-1] = line
            #print(line.replace("\n",""))
            pathstr = str(item.path)
            pathstr = pathstr.replace(str(self._current_root),"")
            deco_path = "%-*s"%(72,deco.path(pathstr))
            deco_lino = "%s %s"%(deco.magenta("Line"),deco.yellow(item.lineno))
            deco_lino = "%-*s"%(37,deco_lino)
            deco_text = deco.val(item.text.strip())
            print("%s%s %s" % (deco_path, deco_lino, deco_text))
        with open(filename,"w") as file:
          file.writelines(lines)
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
  #obt.search.execute_at(words,path_list)
  #########################
  obt.search.visit(find_text, visitor(find_text,replace_text),path_list=path_list)
