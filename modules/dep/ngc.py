from obt import path, pathtools, command, dep, host
from yarl import URL

class ngc(dep.Provider):
  def __init__(self): ############################################
    super().__init__("ngc")
    self.build_dest = path.builds()/"ngc"
    self.dest_bin = path.stage()/"bin"/"ngc"
  def __str__(self):
    return "NGC (nvidia-wget)"
  def download_and_extract(self): #############################################
    dlbase = URL("https://ngc.nvidia.com/downloads")
    HASH = "0"
    fname = ""
    if host.IsOsx and host.IsX86_64:
      HASH = "899ebcbb4743620d52ef1f7e9574b070"
      fname = "ngccli_mac.zip"
    elif host.IsLinux and host.IsX86_64:
      HASH = "17b45d020650adbab3dda22eb271bc39"
      fname = "ngccli_linux.zip"

    url = dlbase/fname
    self.arcpath = dep.downloadAndExtract([url],
                                          fname,
                                          "zip",
                                          HASH,
                                          self.build_dest)
  def build(self): ############################################################
    command.run(["unzip","-o",self.arcpath],working_dir=self.build_dest)
    pathtools.copyfile(self.build_dest/"ngc",self.dest_bin,"u+x")
    "ngc config set"
    "distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
      && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list"

    return self.dest_bin.exists()
  def provide(self): ##########################################################
    OK = self.manifest.exists()
    if False==OK:
      self.download_and_extract()
      OK = self.build()
      if OK:
        self.manifest.touch()
    return OK
