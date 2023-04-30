from ork import dep, pip, path, dep, pathtools, command, log, env
Command = command.Command
from yarl import URL
###############################################################################

VERSION = "master"

class litex(dep.Provider):

  def __init__(self): ############################################
    super().__init__("litex")
    self.OK = self.manifest.exists()
    self.python = self.declareDep("python")

  def build(self): ############################################################
      #PYTHON = dep.instance("python")
      #pip.install(["pytest",
      #             "numpy","scipy",
      #             "numba","pyopencl",
      #             "matplotlib",
      #             "pyzmq","zlib"])
      pathtools.mkdir(self.build_dest,clean=True)
      pathtools.chdir(self.build_dest)
      uri = URL("https://raw.githubusercontent.com")/"enjoy-digital"/"litex"/VERSION/"litex_setup.py"
      commands = [Command(["wget",uri])]
      commands += [Command(["chmod","ugo+x","litex_setup.py"])]
      commands += [Command(["./litex_setup.py","init","install","--user"])]
      commands += [Command(["./litex_setup.py","gcc"])]
      
      for item in commands:
      	ret = item.exec()
      	if ret != 0:
      	  return ret
      return 0

  ########

  def env_init(self):
    log.marker("registering LITEX(%s) SDK"%VERSION)
    LITEX_ROOT = self.build_dest
    LITEX_BOARDS = LITEX_ROOT/"litex-boards"/"litex_boards"
    GCC_RISCV = LITEX_ROOT/"riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14"
    env.set("LITEX_ROOT",LITEX_ROOT)
    env.set("LITEX_BOARDS",LITEX_BOARDS)
    env.append("PATH",LITEX_BOARDS/"targets")
    env.append("PATH",GCC_RISCV/"bin")

  ########

  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "LITEX",
                             environment = dict() )

  ########

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"litex.egg-link").exists()

  def areRequiredBinaryFilesPresent(self):
    return None
