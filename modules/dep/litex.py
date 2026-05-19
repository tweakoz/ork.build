import platform
from obt import dep, pip, path, dep, pathtools, command, log, env
Command = command.Command
from yarl import URL
###############################################################################

VERSION = "master"

# Pinned xPack riscv-none-elf-gcc release for Mac. Anonymous public download
# from xpack-dev-tools' GitHub releases — no Homebrew, no login, no compile.
# Both Apple Silicon (darwin-arm64) and Intel (darwin-x64) Mac binaries
# available. Triple `riscv-none-elf` is in LiteX's CPU_GCC_TRIPLE_RISCV32
# accept-list, so the LiteX firmware Makefile auto-picks it up via PATH.
XPACK_RISCV_VERSION = "14.2.0-3"


def _is_linux(): return platform.system() == "Linux"
def _is_mac():   return platform.system() == "Darwin"


class litex(dep.Provider):

  def __init__(self): ############################################
    super().__init__("litex")
    build_dest = path.builds()/"litex"
    self.build_dest = build_dest
    self.python = self.declareDep("python")
    # Linux and Mac both supported. Linux installs riscv-gcc via the
    # litex_setup.py `gcc` subcommand (apt/dnf/pacman/apk under sudo).
    # Mac installs xPack riscv-none-elf-gcc tarball via _mac_install_xpack
    # below — litex_setup.py's Mac branch (`brew install riscv-tools`) is
    # a dead Homebrew formula and brew refuses to run as root anyway.

  ##############################################################################
  # Mac toolchain helpers
  ##############################################################################

  @property
  def _xpack_arch(self):
    return "darwin-arm64" if platform.machine() == "arm64" else "darwin-x64"

  @property
  def _xpack_dir(self):
    """Fixed extraction dir under build_dest. Stable across version bumps
    (we tar-extract with --strip-components=1 so the inner version-suffixed
    directory is collapsed)."""
    return self.build_dest/"riscv-none-elf-gcc"

  @property
  def _xpack_bin(self):
    return self._xpack_dir/"bin"

  def _patch_litex_setup_for_mac(self):
    """Replace litex_setup.py's dead Mac branch with an informational
    no-op. Defense-in-depth — our build() bypasses the `gcc` subcommand
    on Mac entirely, but a user invoking `./litex_setup.py gcc` manually
    in build_dest would otherwise hit the brew error."""
    p = self.build_dest/"litex_setup.py"
    if not p.exists():
      return
    txt = p.read_text()
    old = 'subprocess.check_call(["brew", "install", "riscv-tools"])'
    new = ('print("[litex_setup.py] macOS: skipped `brew install riscv-tools` "\n'
           '              "(formula removed from Homebrew core; brew also refuses sudo).\\n"\n'
           '              "  Install riscv-none-elf-gcc via xPack tarball, "\n'
           '              "`brew tap riscv-software-src/riscv && brew install riscv-gnu-toolchain`, "\n'
           '              "or any other method, and put it on PATH.\\n"\n'
           '              "  The OBT litex dep installs xPack riscv-none-elf-gcc automatically — "\n'
           '              "you should not need to run this subcommand on Mac.")')
    if old in txt:
      p.write_text(txt.replace(old, new))

  def _mac_install_xpack(self):
    """Download + extract xPack riscv-none-elf-gcc tarball under
    build_dest/riscv-none-elf-gcc. Anonymous HTTPS GET from the
    xpack-dev-tools GitHub release. No Homebrew, no login, no compile.
    Returns True on success (Provider.provide() truthy convention)."""
    pathtools.mkdir(self._xpack_dir, clean=True)
    # No chdir — each Command runs in self.build_dest via working_dir.
    tarball = (f"xpack-riscv-none-elf-gcc-{XPACK_RISCV_VERSION}-"
               f"{self._xpack_arch}.tar.gz")
    url = ("https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/"
           f"releases/download/v{XPACK_RISCV_VERSION}/{tarball}")
    cmds = [
      Command(["curl", "-fL", "-o", tarball, url],
              working_dir=self.build_dest),
      # --strip-components=1 collapses the version-suffixed top dir
      # (xpack-riscv-none-elf-gcc-<ver>/) so bin/lib/include land
      # directly under self._xpack_dir.
      Command(["tar", "xzf", tarball, "-C", str(self._xpack_dir),
               "--strip-components=1"],
              working_dir=self.build_dest),
      Command(["rm", tarball], working_dir=self.build_dest),
    ]
    for c in cmds:
      if c.exec() != 0:
        return False
    return True

  ##############################################################################

  def build(self): ############################################################
    """Provider.provide() expects a truthy return on success — return True
    when every stage succeeds, False on the first failed Command. Returning
    a shell exit code (0) here would be falsy and trip the post-build
    `if OK:` gate that calls `manifest.touch()`."""
    pathtools.mkdir(self.build_dest, clean=True)
    # No chdir — each Command runs in self.build_dest via working_dir.
    uri = URL("https://raw.githubusercontent.com")/"enjoy-digital"/"litex"/VERSION/"litex_setup.py"

    # Stage 1 — fetch litex_setup.py and patch its dead Mac branch.
    for c in [Command(["wget", uri], working_dir=self.build_dest),
              Command(["chmod", "ugo+x", "litex_setup.py"],
                      working_dir=self.build_dest)]:
      if c.exec() != 0:
        return False
    self._patch_litex_setup_for_mac()

    # Stage 2 — clone repos / install Python packages / OS-specific GCC.
    commands = [Command(["./litex_setup.py", "init", "install"],
                        working_dir=self.build_dest)]
    if _is_linux():
      commands += [Command(["echo", "building litex unfortunately requires sudo for now.."],
                           working_dir=self.build_dest)]
      commands += [Command(["sudo", "./litex_setup.py", "gcc"],
                           working_dir=self.build_dest)]
    # Mac: bypass `litex_setup.py gcc` — see _mac_install_xpack below.
    commands += [Command(["pip3", "install",
                          "git+https://github.com/litex-hub/pythondata-software-picolibc.git"],
                         working_dir=self.build_dest)]
    commands += [Command(["pip3", "install", "meson"],
                         working_dir=self.build_dest)]
    for c in commands:
      if c.exec() != 0:
        return False

    # Stage 3 — Mac toolchain (xPack riscv-none-elf-gcc).
    if _is_mac():
      if not self._mac_install_xpack():
        return False

    return True

  ########

  def env_init(self):
    LITEX_ROOT = self.build_dest
    if not LITEX_ROOT.exists():
      return
    log.marker("registering LITEX(%s) SDK" % VERSION)
    LITEX_BOARDS = LITEX_ROOT/"litex-boards"/"litex_boards"
    env.set("LITEX_ROOT", LITEX_ROOT)
    env.set("LITEX_BOARDS", LITEX_BOARDS)
    env.append("PATH", LITEX_BOARDS/"targets")
    if _is_linux():
      GCC_RISCV = LITEX_ROOT/"riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14"
      env.append("PATH", GCC_RISCV/"bin")
    elif _is_mac():
      env.append("PATH", self._xpack_bin)

  def env_goto(self):
    return {"litex": self.build_dest}

  ########

  def on_build_shell(self):
    pathtools.mkdir(self.build_dest, clean=False)
    return command.subshell(directory=self.build_dest,
                            prompt="LITEX",
                            environment=dict())

  ########

  def areRequiredSourceFilesPresent(self):
    return (self.build_dest/"setup.py").exists()

  def areRequiredBinaryFilesPresent(self):
    base = (self.build_dest/"litex-boards"/"litex_boards"
            /"targets"/"digilent_nexys4.py").exists()
    if _is_mac():
      return base and (self._xpack_bin/"riscv-none-elf-gcc").exists()
    return base
