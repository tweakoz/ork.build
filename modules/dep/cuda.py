from obt import host, dep, path, osrelease

###############################################################################

class cuda(dep.Provider):

  def __init__(self): ############################################
    super().__init__("cuda")
    self._oslist = ["Linux"]

  ########

  def __str__(self):
    return "cuda (system)"

  ########

  @property
  def cxx_compiler(self):
    if host.IsDebian:
      desc = host.description()
      if desc.codename=="mantic":
        return "g++-12"
      elif desc.codename=="jammy":
        return "g++-9"
      else:
        return "g++-8"
    return "g++"
  @property
  def c_compiler(self):
    if host.IsDebian:
      desc = host.description()
      if desc.codename=="mantic":
        return "gcc-12"
      elif desc.codename=="jammy":
        return "gcc-9"
      else:
        return "gcc-8"
    return "gcc"

  ########

  #wget http://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers/cuda_11.0.2_450.51.05_linux.run


  def provide(self): ##########################################################
    self.manifest.touch()
    return True

  def areRequiredSourceFilesPresent(self):
    return path.Path("/usr/bin/nvcc").exists()
  def areRequiredBinaryFilesPresent(self):
    return path.Path("/usr/bin/nvcc").exists()


#/usr/local/cuda-10.2
