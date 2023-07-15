from obt import template, path

class Generator:

  def __init__(self):
    self.template_str = ""

  def try_add_item(self,varname,key):
    if key in self.replacements.keys():
      val = self.replacements[key]
      if val != "":
        print(key,val,varname)
        self.template_str += "%s: %s\n" % (varname,str(val))

  def apply(self,replacements,outpath=None):
    self.replacements = replacements
    self.try_add_item("prefix","PREFIX")
    self.try_add_item("exec_prefix","PREFIX")
    self.try_add_item("includedir","PREFIX/include")
    self.try_add_item("Name","NAME")
    self.try_add_item("Description","DESCRIPTION")
    self.try_add_item("Requires","REQUIRES")
    self.try_add_item("Version","VERSION")
    self.try_add_item("Libs.private","LIBS_PRIVATE")
    self.try_add_item("Libs","LIBS_PUBLIC")
    self.try_add_item("Cflags","CFLAGS")

    #print(self.template_str,replacements)
    #out = template.template_string(self.template_str,replacements)
    #print( "#################################")
    #print(self.template_str)
    #print( "#################################")

    if outpath!=None:
      with open(str(outpath),"w") as outfile:
        outfile.write(self.template_str)

    return self.template_str