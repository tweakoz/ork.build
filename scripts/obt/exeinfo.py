#!/usr/bin/env python3

from obt import command, host

def _getLinkedLibrariesLinux(executable_path):

  result = command.capture(["ldd", executable_path])
  libraries = {}
  for line in result.strip().split("\n"):
    parts = [part.strip() for part in line.split("=>")]
    lib_name = parts[0].split(" ")[0]
    
    if len(parts) > 1:
      lib_path = parts[1].split(" ")[0]
    else:
      lib_path = None  # Some system libraries might not have a path

    libraries[lib_name] = lib_path

  return libraries

def getLinkedLibraries(executable_path):
  if host.IsLinux:
    return _getLinkedLibrariesLinux(executable_path)
  else:
    assert(False)
    return None
