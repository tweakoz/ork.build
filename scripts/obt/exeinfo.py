#!/usr/bin/env python3

from obt import command, host

def _getLinkedLibrariesLinux(executable_path, unique_set, libraries):
  result = command.capture(["ldd", executable_path])
  for line in result.strip().split("\n"):
    parts = [part.strip() for part in line.split("=>")]
    lib_name = parts[0].split(" ")[0]
    if len(parts) > 1:
      lib_path = parts[1].split(" ")[0]
    else:
      lib_path = None  # Some system libraries might not have a path
    libraries[lib_name] = lib_path
    if lib_path and lib_path not in unique_set:
      unique_set.add(lib_path)
      _getLinkedLibrariesLinux(lib_path, unique_set,libraries)

def getLinkedLibraries(executable_path):
  unique_set = set()
  libraries = {}
  if host.IsLinux:
    _getLinkedLibrariesLinux(executable_path,unique_set,libraries)
    return libraries
  else:
    assert(False)
    return None
