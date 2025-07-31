#!/usr/bin/env python3

import os
import sys
import site
import obt.path
import importlib.metadata
from obt.deco import Deco
deco = Deco()

# Column width constants
COL_FOLDER = 28
COL_STATE = 10
COL_BRANCH = 20
COL_HASH = 14
COL_MESSAGE = 40

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
    
    # Get current branch name
    try:
        branch = repo.active_branch.name
    except TypeError:
        # HEAD is detached
        branch = "detached HEAD"
    
    # Get commit message (first line only)
    message = repo.head.object.message.split('\n')[0]
    
    return hash, is_dirty, branch, message
  except git.InvalidGitRepositoryError:
    return None, None, None, None

def truncate_with_ellipsis(text, max_width):
    """Truncate text to fit within max_width, adding ellipsis if needed"""
    if len(text) > max_width:
        return text[:max_width-3] + "..."
    return text

def reverse_video(text):
    """Apply reverse video (swap foreground/background) to text"""
    return f"\033[7m{text}\033[0m"

def center_text(text, width):
    """Center text within given width"""
    return text.center(width)

# Print header if there are git projects
if project_list and any(obt.path.Path(item).exists() for item in project_list):
    print( "######################################################")
    print(deco.key("Git Repositories:"))
    print()
    
    # Print reverse video header with centered column labels
    header_row = (
        center_text("REPOSITORY", COL_FOLDER - 6).rjust(COL_FOLDER) +
        center_text("STATE", COL_STATE) +
        center_text("BRANCH", COL_BRANCH) +
        center_text("COMMIT", COL_HASH) +
        center_text("MESSAGE", COL_MESSAGE)
    )
    print(reverse_video(header_row))

for item in project_list:
  item = obt.path.Path(item)
  if item.exists():
    os.chdir(item)
    git_hash, is_dirty, branch, message = get_git_info()
    if git_hash:
      # Prepare folder name - check if it matches any environment variable
      folder_name = str(item)
      
      # Check all environment variables for exact match, excluding common ones
      env_var_name = None
      excluded_vars = {'PWD', 'OLDPWD', 'HOME', 'PATH', 'SHELL', 'USER', 'LOGNAME', 
                       'TERM', 'LANG', 'LC_ALL', 'LC_CTYPE', 'DISPLAY', 'EDITOR',
                       'VISUAL', 'TMPDIR', 'TMP', 'TEMP', 'HOSTNAME', 'PS1', 'PS2',
                       'PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE',
                       'PYTHONEXECUTABLE', 'PYTHONWARNINGS', 'PYTHONNOUSERSITE',
                       'PYTHONUNBUFFERED', '_'}
      
      for key, value in os.environ.items():
        if key not in excluded_vars and value == folder_name:
          env_var_name = key
          break
      
      # Use env var name if found, otherwise use folder path
      if env_var_name:
        folder_display = truncate_with_ellipsis(f"${env_var_name}", COL_FOLDER - 1)
      else:
        folder_display = truncate_with_ellipsis(folder_name, COL_FOLDER - 1)
      
      # Prepare branch name
      branch_display = truncate_with_ellipsis(branch, COL_BRANCH - 1)
      
      # Prepare message
      message_display = truncate_with_ellipsis(message, COL_MESSAGE - 1)
      
      # Color elements (reordered: folder, state, branch, hash, message)
      # Right-justify repo folder
      colored_folder = deco.val(folder_display.rjust(COL_FOLDER))
      
      # Color and center status
      if is_dirty:
        status_text = "modified"
        colored_status = deco.red(status_text.center(COL_STATE))
      else:
        status_text = "clean"
        colored_status = deco.rgbstr(0, 255, 0, status_text.center(COL_STATE))
      
      # Center branch and hash
      colored_branch = deco.rgbstr(191, 191, 191, branch_display.center(COL_BRANCH))
      colored_hash = deco.rgbstr(255, 179, 51, git_hash[:8].center(COL_HASH))
      
      # Left-justify message (already left-justified by default)
      colored_message = deco.rgbstr(128, 192, 255, message_display.ljust(COL_MESSAGE))
      
      # Print formatted line (reordered columns)
      print(f"{colored_folder}{colored_status}{colored_branch}{colored_hash}{colored_message}")
    else:
      print(f"{deco.val(str(item).ljust(COL_FOLDER))}{deco.red('not a repo')}")