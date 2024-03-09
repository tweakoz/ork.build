from obt import subspace, path

def exists(name):
  if subspace.targeting_host():
    manifest = path.subspace_dir()/"manifest"
    if (manifest/name).exists():
      return True
    else:
      manifest = path.stage_dir()/"manifest"
      return (manifest/name).exists()
  else:
    manifest = path.subspace_dir()/"manifest"
    return (manifest/name).exists()