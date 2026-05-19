###############################################################################
# Orkid Build Tools
# Per-thread stdout/stderr capture for the parallel build pipeline.
#
# The pipeline's worker threads share the process's sys.stdout / sys.stderr
# and Popen's inherited fd 1/fd 2. Without per-thread redirection the output
# of N concurrent fetches/builds interleaves into an unreadable mess and any
# TUI overlay gets blown out by subprocess output.
#
# This module installs a thread-aware proxy on sys.stdout / sys.stderr, plus
# a context manager that workers use to point their thread's output at a log
# file. The same fd is registered as a thread-local hint in obt.command so
# Command.exec() picks it up automatically when invoking subprocesses.
###############################################################################

import io
import sys
import threading


class _ThreadStream:
  """Stream wrapper. Writes go to a thread-local stream if one has been set
  via set_thread_stream(); otherwise fall through to the wrapped default
  stream. isatty() always returns the default stream's value (so callers
  that probe for color support still get an honest answer)."""

  def __init__(self, default):
    self._default = default
    self._tlocal  = threading.local()

  def write(self, s):
    f = getattr(self._tlocal, "stream", None)
    if f is None:
      return self._default.write(s)
    return f.write(s)

  def flush(self):
    f = getattr(self._tlocal, "stream", None)
    if f is None:
      self._default.flush()
    else:
      try:
        f.flush()
      except Exception:
        pass

  def isatty(self):
    try:
      return self._default.isatty()
    except Exception:
      return False

  def fileno(self):
    f = getattr(self._tlocal, "stream", None)
    if f is None:
      return self._default.fileno()
    return f.fileno()

  def __getattr__(self, name):
    return getattr(self._default, name)

  def set_thread_stream(self, stream):
    self._tlocal.stream = stream

  def clear_thread_stream(self):
    self._tlocal.stream = None


_install_lock = threading.Lock()
_installed    = False
_orig_stdout  = None
_orig_stderr  = None
_stdout_proxy = None
_stderr_proxy = None


def install():
  """Idempotent. Replace sys.stdout / sys.stderr with thread-aware proxies."""
  global _installed, _orig_stdout, _orig_stderr, _stdout_proxy, _stderr_proxy
  with _install_lock:
    if _installed:
      return
    _orig_stdout = sys.stdout
    _orig_stderr = sys.stderr
    _stdout_proxy = _ThreadStream(sys.stdout)
    _stderr_proxy = _ThreadStream(sys.stderr)
    sys.stdout = _stdout_proxy
    sys.stderr = _stderr_proxy
    _installed = True


def uninstall():
  global _installed
  with _install_lock:
    if not _installed:
      return
    sys.stdout = _orig_stdout
    sys.stderr = _orig_stderr
    _installed = False


def is_installed():
  return _installed


class redirect_thread_io:
  """Context manager: while active, this thread's writes to sys.stdout /
  sys.stderr go to `path` (appended). Subprocess inheritance is handled
  separately by obt.command's thread-local fd hint, which we also set here.

  Both Python prints and subprocess output (via Command.exec()) end up in
  the same log file.

  Usage:
      with redirect_thread_io(Path("/tmp/foo.log")):
          provider.fetch_only()
  """

  def __init__(self, path):
    self.path = str(path)
    self.file = None

  def __enter__(self):
    if not _installed:
      install()
    # Open with explicit O_CLOEXEC. Python's open() does this by default
    # (PEP 446) but being explicit guards against any path that might
    # inherit this fd through fork+exec chains we don't control. The
    # subprocess inheritance for stdout/stderr happens via Popen's dup2
    # mapping, not by direct fd inheritance — Popen takes care of it.
    import os as _os
    flags = _os.O_WRONLY | _os.O_CREAT | _os.O_APPEND | _os.O_CLOEXEC
    raw_fd = _os.open(self.path, flags, 0o644)
    # Wrap in line-buffered text mode so Python print()s flush at newlines.
    self.file = _os.fdopen(raw_fd, "a", buffering=1, encoding="utf-8",
                           errors="replace")
    _stdout_proxy.set_thread_stream(self.file)
    _stderr_proxy.set_thread_stream(self.file)
    # Tell obt.command to pass this fd to subprocess.Popen by default.
    from obt import command as _cmd
    _cmd._set_thread_log_fd(self.file.fileno())
    return self

  def __exit__(self, *exc):
    from obt import command as _cmd
    _cmd._clear_thread_log_fd()
    if _stdout_proxy is not None:
      _stdout_proxy.clear_thread_stream()
    if _stderr_proxy is not None:
      _stderr_proxy.clear_thread_stream()
    if self.file is not None:
      try:
        self.file.close()
      except Exception:
        pass
      self.file = None
    return False  # don't swallow exceptions
