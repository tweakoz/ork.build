import obt.deco
import obt.path
import obt.template
from obt.command import Command
import fileinput

deco = obt.deco.Deco()

class patcher:

  def __init__(self,provider,repl_dict=None):
    name = provider._name
    self._ori = obt.path.patches(provider)/name/"ori"
    self._chg = obt.path.patches(provider)/name/"chg"
    self._repl_dict = repl_dict

  def patch(self,dest_dir,file):
    src  = self._chg/file
    dest = dest_dir/file
    print("Patching <%s -> %s>" % (deco.bright(src), deco.yellow(dest)))
    Command(["cp","-f",src,dest]).exec()
    if self._repl_dict:
      obt.template.template_file(dest,self._repl_dict)

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


def patch_with_diffstr(file_path, diff_str):
    import os
    import subprocess
    import tempfile
    """
    Applies a unified diff (diff_str) to the specified file_path using the 'patch' command.

    :param diff_str: A string containing the unified diff.
    :param file_path: The path to the file that the diff should be applied to.
    :raises subprocess.CalledProcessError: If 'patch' exits with a non-zero status.
    """
    # Create a temporary file to store the diff
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_patch:
        temp_patch.write(diff_str)
        temp_patch.flush()
        temp_patch_path = str(temp_patch.name)

    try:
        # Call the system 'patch' command
        subprocess.check_call(["patch", str(file_path), temp_patch_path])
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_patch_path):
            os.remove(temp_patch_path)
