#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string
import ork.path
from ork.path import Path
import ork.deco
deco = ork.deco.Deco()

#################################################################################

def find(word):
 def _find(path):
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

def search_at_root(word, root):
 finder = find(word)
 results = list()
 for root, dirs, files in os.walk(root):
  for f in files:
   path = os.path.join(root, f)
   spl = os.path.splitext(path)
   ext = spl[1]
   not_obj = (spl[0].find("/obj/")==-1) and (spl[0].find("/pluginobj/")==-1)
   if not_obj:
    if ext in ext_set:
     for line_number, line in finder(path):
      line = line.replace("\n","")
      res = result(path,line_number,line)
      results.append(res)
 return results

#################################################################################

pthspec = []

#################################################################################

if "ORK_FIND_PATH" in os.environ:
  p = os.environ["ORK_FIND_PATH"]
  pthspec = p.split(":")
else:
  p = os.environ["OBT_ROOT"]
  pthspec = p.split(":")

#################################################################################

print(pthspec)
pathlist = []
for p in pthspec:
  pathlist += [Path(p)]

print(pathlist)

#################################################################################

def execute(word):
  for path in pathlist:
   results = search_at_root(word,str(path))
   have_results = len(results)!=0
   if have_results:
    print("/////////////////////////////////////////////////////////////")
    print("// path : %s" % path)
    print("/////////")
    root = str(ork.path.project_root())+"/"
    for item in results:
      pathstr = str(item.path)
      pathstr = pathstr.replace(str(root),"")
      deco_path = "%-*s"%(72,deco.path(pathstr))
      deco_lino = "%s %s"%(deco.magenta("Line"),deco.yellow(item.lineno))
      deco_lino = "%-*s"%(37,deco_lino)
      deco_text = deco.val(item.text.strip())
      print("%s%s %s" % (deco_path, deco_lino, deco_text))



#################################################################################

def visit(word,visitor):
  for path in pathlist:
   results = search_at_root(word,str(path))
   have_results = len(results)!=0
   if have_results:
     visitor.onPath(path)
     for item in results:
       visitor.onItem(item)
