###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from string import Template
import obt.deco
deco = obt.deco.Deco()

####################################################################

class OrkTemplate(Template):
  delimiter = "$$$" # override delimiter because sometimes we do files with $ in them

####################################################################

def template_file(inppath, replacements, outpath=None):

    if outpath==None:
       outpath = inppath # (inplace)

    print("Applying template to %s"%deco.path(outpath))

    inpstr = ""
    with open(str(inppath),"r") as f:
        inpstr = f.read()
    with open(str(outpath),"w") as outfile:
        t = OrkTemplate(inpstr)
        print(inpstr)
        print(t)
        print(replacements)
        outstr = t.substitute(replacements)
        print(outstr)
        outfile.write(outstr)

####################################################################

def template_string(inpstring, replacements, outpath=None):

  t = OrkTemplate(inpstring)
  outstr = t.substitute(replacements)

  if outpath!=None:
    with open(str(outpath),"w") as outfile:
      outfile.write(outstr)

  return outstr

####################################################################
