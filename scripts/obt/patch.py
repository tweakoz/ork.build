import ork.deco
import ork.path
import ork.template
from ork.command import Command
import fileinput

deco = ork.deco.Deco()

class patcher:

  def __init__(self,provider,repl_dict=None):
    name = provider._name
    self._ori = ork.path.patches(provider)/name/"ori"
    self._chg = ork.path.patches(provider)/name/"chg"
    self._repl_dict = repl_dict

  def patch(self,dest_dir,file):
    src  = self._chg/file
    dest = dest_dir/file
    print("Patching <%s -> %s>" % (deco.bright(src), deco.yellow(dest)))
    Command(["cp","-f",src,dest]).exec()
    if self._repl_dict:
      ork.template.template_file(dest,self._repl_dict)

  def patch_list(self,list_of_items):
    for i in list_of_items:
      print(i)
      self.patch(i[0],i[1])


def patch_with_dict(filename,item_dict):
  for k in item_dict.keys():
    v = item_dict[k]
    with fileinput.FileInput(str(filename), inplace=True, backup='.bak') as file:
      for line in file:
        print(line.replace(k, v), end='')
