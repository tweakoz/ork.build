#!/usr/bin/env python3 

import os
import sys
import site
import obt.path
import importlib.metadata
from obt.deco import Deco
deco = Deco()

def print_env_var(name, default):
    value = os.getenv(name, default)
    print(f"{deco.key(name)}: {deco.val(value)}")

def print_item(name, value):
    print(f"{deco.key(name)}: {deco.val(value)}")

print( "######################################################")

print_env_var(f'PYTHONPATH', sys.path)
print_env_var(f'PYTHONHOME', sys.prefix)
print_env_var(f'PYTHONSTARTUP', 'Not set')
print_env_var(f'PYTHONUSERBASE', site.USER_BASE)
print_env_var(f'PYTHONEXECUTABLE', sys.executable)
print_env_var(f'PYTHONWARNINGS', 'Not set')
print_env_var(f'PYTHONNOUSERSITE', 'Not set (User site directory is added to sys.path)')
print_env_var(f'PYTHONUNBUFFERED', 'Not set (Buffered I/O is used for stdout and stderr)')

print_env_var(f'site.PREFIXES', site.PREFIXES)
print_env_var(f'site.USER_SITE', site.USER_SITE)
print_env_var(f'site.USER_BASE', site.USER_BASE)
print_env_var(f'sys.prefix', sys.prefix)
print_env_var(f'sys.base_prefix', sys.base_prefix)

print( "######################################################")

a = importlib.metadata.distribution("ork.build").metadata

print_item( "obt-pymodule-path",obt.path.obt_module_path() )
print_item( "obt-data-base",obt.path.obt_data_base() )
print_item( "obt-modules-test",obt.path.__get_modules() )
print_item( "obt-test-inplace",obt.path.__is_inplace() )
print_item( "obt-modules-base",obt.path.obt_modules_base() )
print_item( "running_from_pip",obt.path.running_from_pip() )
print_item( "running_in_tree",obt.path.obt_in_tree() )
print_item( "obt.distrib.name",a["Name"] )
print_item( "obt.distrib.author",a["Author"] )
print_item( "obt.distrib.author-email",a["Author-email"] )
print_item( "obt.distrib.summary",a["Summary"] )
print_item( "obt.distrib.homepage",a["Home-page"] )
print( "################################################")
print_item( "obt.distrib.version",a["Version"] )


plist = os.environ.get("OBT_PROJECTS_LIST", "")
project_list = plist.split(":") if plist else []

def get_git_info():
  import git
  try:
    repo = git.Repo(search_parent_directories=True)
    hash = repo.head.object.hexsha
    is_dirty = repo.is_dirty(untracked_files=True)
    return hash, is_dirty
  except git.InvalidGitRepositoryError:
    return None, None    

for item in project_list:
  item = obt.path.Path(item)
  if item.exists():
    os.chdir(item)
    git_hash, is_dirty = get_git_info()
    if git_hash:
      status = "modified" if is_dirty else "clean"
      print_item(f"OBTGITPRJ: {item}", f"{git_hash[:8]} ({status})")
    else:
      print_item(f"OBTGITPRJ: {item}", f"not a repo")