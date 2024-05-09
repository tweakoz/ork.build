from obt import dep, pip, path, dep, pathtools, command, log, env
Command = command.Command
from yarl import URL
###############################################################################

VERSION = "master"

class litex(dep.Provider):

  def __init__(self): ############################################
    super().__init__("litex")
    build_dest = path.builds()/"litex"
    self.build_dest = build_dest
    self.python = self.declareDep("python")
    self._oslist = ["Linux"]
    self._archlist = ["x86_64"]

  def build(self): ############################################################
      pathtools.mkdir(self.build_dest,clean=True)
      pathtools.chdir(self.build_dest)
      uri = URL("https://raw.githubusercontent.com")/"enjoy-digital"/"litex"/VERSION/"litex_setup.py"
      commands = [Command(["wget",uri])]
      commands += [Command(["chmod","ugo+x","litex_setup.py"])]
      commands += [Command(["./litex_setup.py","init","install"])]
      commands += [Command(["echo", "building litex unfortunately requires sudo for now.."])]
      commands += [Command(["sudo","./litex_setup.py","gcc"])]
      commands += [Command(["pip3","install","git+https://github.com/litex-hub/pythondata-software-picolibc.git"])]
      commands += [Command(["pip3","install","meson"])]

      for item in commands:
      	ret = item.exec()
      	if ret != 0:
      	  return ret
      return 0

  ########

  def env_init(self):
    LITEX_ROOT = self.build_dest
    if LITEX_ROOT.exists():
      log.marker("registering LITEX(%s) SDK"%VERSION)
      LITEX_BOARDS = LITEX_ROOT/"litex-boards"/"litex_boards"
      GCC_RISCV = LITEX_ROOT/"riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14"
      env.set("LITEX_ROOT",LITEX_ROOT)
      env.set("LITEX_BOARDS",LITEX_BOARDS)
      env.append("PATH",LITEX_BOARDS/"targets")
      env.append("PATH",GCC_RISCV/"bin")

  def env_goto(self):
    return { "litex": self.build_dest }

  ########

  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "LITEX",
                             environment = dict() )

  ########

  def areRequiredSourceFilesPresent(self):
    return (self.build_dest/"setup.py").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.build_dest/"litex-boards"/"litex_boards"/"targets"/"digilent_nexys4.py").exists()
