from obt import subspace, path

###########################################################

def exists(name):
  
  if subspace.is_host_subspace():
    manifest = path.subspace_dir()/"manifest"
    if (manifest/name).exists():
      return True
    else:
      manifest = path.stage()/"manifest"
      return (manifest/name).exists()
  else:
    manifest = path.subspace_dir()/"manifest"
    return (manifest/name).exists()