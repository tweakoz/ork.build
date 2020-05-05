from string import Template
import ork.deco
deco = ork.deco.Deco()

class OrkTemplate(Template):
  delimiter = "$$$" # override delimiter because sometimes we do files with $ in them

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
        outfile.write(outstr)
