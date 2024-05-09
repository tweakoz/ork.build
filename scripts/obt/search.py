#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string
import obt.path
import obt.dep
from obt.path import *
import obt.deco
deco = obt.deco.Deco()

#################################################################################

def find(word):
 def _find(path):
  if os.path.exists(str(path)):
    with open(path, "rb") as fp:
     for n, line in enumerate(fp):
      try:
        line_as_str = line.decode("utf-8")
        if word in line_as_str:
          yield n+1, line_as_str
      except Exception:
        pass
 return _find

#################################################################################

class result:
 def __init__(self,path,lineno,text):
  self.path = path
  self.lineno = lineno
  self.text = text

#################################################################################

ext_set = set(os.environ["OBT_SEARCH_EXTLIST"].split(":"))

#################################################################################

ignore_folder_keys = set(["/obj/", "/pluginobj/","/.build/"])

#################################################################################

def search_at_root(word, root,ignore_set = ignore_folder_keys):
 finder = find(word)
 results = list()
 for root, dirs, files in os.walk(root):
  for f in files:
   path = os.path.join(root, f)
   spl = os.path.splitext(path)
   ext = spl[1]
   ignore = False
   for item in ignore_set:
       if (spl[0].find(item)!=-1):
           ignore = True
   if not ignore:
    if (finder!=None) and ext in ext_set:
     for line_number, line in finder(path):
      line = line.replace("\n","")
      res = result(path,line_number,line)
      results.append(res)
 return results

#################################################################################

p = os.environ["OBT_ROOT"]
pthspec = p.split(":")

#################################################################################

if "OBT_SEARCH_PATH" in os.environ:
  p = os.environ["OBT_SEARCH_PATH"]
  pthspec += p.split(":")

#################################################################################

#print(pthspec)
default_pathlist = []
for p in pthspec:
  default_pathlist += [Path(p)]

#################################################################################

def execute(word,path_list = default_pathlist):
  for path in path_list:
   results = search_at_root(word,str(path))
   have_results = len(results)!=0
   if have_results:
    print("/////////////////////////////////////////////////////////////")
    print("// path : %s" % path)
    print("/////////")
    root = str(obt.path.project_root())+"/"
    for item in results:
      pathstr = str(item.path)
      pathstr = pathstr.replace(str(root),"")
      deco_path = "%-*s"%(72,deco.path(pathstr))
      deco_lino = "%s %s"%(deco.bright("Line"),deco.yellow(item.lineno))
      deco_lino = "%-*s"%(37,deco_lino)
      deco_text = deco.val(item.text.strip())
      print("%s%s %s" % (deco_path, deco_lino, deco_text))

#################################################################################

def execute_at(word_list,path_list,remove_root=None):
  for path in path_list:
   print("/////////////////////////////////////////////////////////////")
   print("// searching path : %s" % path)
   print("/////////")
   for word in word_list:
     results = search_at_root(word,str(path))
     have_results = len(results)!=0
     if have_results:
       for item in results:
         pathstr = str(item.path)
         if remove_root!=None:
           r_root = str(remove_root)+"/"
           pathstr = pathstr.replace(str(r_root),"")
         deco_path = "%-*s"%(72,deco.path(pathstr))
         deco_lino = "%s %s"%(deco.magenta("Line"),deco.yellow(item.lineno))
         deco_lino = "%-*s"%(37,deco_lino)
         deco_text = deco.val(item.text.strip())
         print("%s%s %s" % (deco_path, deco_lino, deco_text))


#################################################################################

def visit(word,visitor, path_list = default_pathlist):
  for path in path_list:
   results = search_at_root(word,str(path))
   have_results = len(results)!=0
   print(have_results)
   if have_results:
     visitor.onPath(path)
     for item in results:
       visitor.onItem(item)
