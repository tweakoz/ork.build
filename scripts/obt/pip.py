import os, shutil, threading
import obt.deco
from obt import path, dep
from obt.command import Command
from obt.retry import retry_until_rc_zero

# pip is not safe to invoke concurrently — `pip install` writes to
# site-packages without any cross-process locking, so two concurrent installs
# can corrupt the python environment. This module-level lock serializes all
# pip operations within a single process (the parallel pipeline scheduler).
_pip_lock = threading.Lock()

def _clean_build_dir(name_or_list):
  """Remove build/ directory for local path installs to avoid stale artifacts."""
  items = [name_or_list] if isinstance(name_or_list, str) else name_or_list
  for item in items:
    p = os.path.abspath(item)
    if os.path.isdir(p):
      build_dir = os.path.join(p, "build")
      if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

def _command(name_or_list,cmd):
  #Command().exec()
  #pip_executable = path.stage()/"bin"/"pip3"
  PYTHON = dep.instance("python")
  python_executable = PYTHON.executable
  cmd_prefix = [python_executable,"-m","pip",cmd]

  if cmd == "install":
    _clean_build_dir(name_or_list)

  if isinstance(name_or_list, str):
    argv = cmd_prefix + [name_or_list]
    label_target = name_or_list
  else:
    argv = cmd_prefix + name_or_list
    label_target = ",".join(name_or_list)

  with _pip_lock:
    return retry_until_rc_zero(
        lambda: Command(argv).exec(),
        label="pip %s %s" % (cmd, label_target),
    )

def install(name_or_list):
  return _command(name_or_list,"install")

def uninstall(name_or_list):
  return _command(name_or_list,"uninstall")
