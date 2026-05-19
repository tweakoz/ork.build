###############################################################################
# Orkid Build Tools
# Rich-based TUI for the parallel build pipeline.
#
# Renders three live-updating panels: in-flight fetches, in-flight builds,
# and recent terminal-state deps. The scheduler updates the underlying
# state dict and started_at dict under its lock; a background UI thread
# polls and re-renders at 4 Hz.
#
# Gracefully degrades to a no-op stub when:
#   - rich is not installed,
#   - stdout is not a TTY (CI / log redirection),
#   - the caller explicitly asks for plain mode.
###############################################################################

import os
import re
import sys
import threading
import time
from collections import deque

try:
  from rich.columns import Columns
  from rich.console import Console, Group
  from rich.live import Live
  from rich.panel import Panel
  from rich.table import Table
  from rich.text import Text
  _HAS_RICH = True
except ImportError:
  _HAS_RICH = False


def _fmt_elapsed(secs):
  m, s = divmod(int(secs), 60)
  if m >= 60:
    h, m = divmod(m, 60)
    return "%dh %02dm %02ds" % (h, m, s)
  return "%dm %02ds" % (m, s)


###############################################################################
# Build-progress scraper: scans the tail of a dep's log file for cmake / make /
# ninja / autoconf progress lines and returns (label, activity) suitable for
# display in the in-flight panel.
###############################################################################

_NINJA_RE        = re.compile(r"^\[(\d+)/(\d+)\]\s+(.*)")
_MAKE_PCT_RE     = re.compile(r"^\[\s*(\d+)%\]\s+(.*)")
_CMAKE_INSTALL_RE = re.compile(r"^-- Installing:\s+(.*)")
_CMAKE_DASH_RE   = re.compile(r"^-- (.+)")
_AUTOCONF_RE     = re.compile(r"^checking\s+(.+?)\.\.\.\s*(.*)$")

# Lines we ignore — they're too noisy or uninformative to display.
_IGNORE_PREFIXES = (
    "[fetch]", "[build]", "[prelude]", "[scheduler]",
    "=" * 5,
)


def _truncate(s, n=48):
  s = s.strip()
  return s if len(s) <= n else s[: n - 1] + "…"


class LogTailer:
  """Reads the tail of growing log files and parses build-progress lines.
  Results are size-cached so repeated reads of an unchanged log are cheap."""

  def __init__(self, tail_bytes=16384, max_scan_lines=200):
    self.tail_bytes     = tail_bytes
    self.max_scan_lines = max_scan_lines
    self._cache         = {}   # path -> (size_snapshot, parsed_result_or_None)

  def scan(self, path):
    """Return (label, activity) tuple of strings, or None if no useful info."""
    try:
      st = path.stat()
    except OSError:
      return None
    size = st.st_size
    cached = self._cache.get(path)
    if cached is not None and cached[0] == size:
      return cached[1]
    try:
      with open(path, "rb") as f:
        if size > self.tail_bytes:
          f.seek(-self.tail_bytes, 2)
          f.readline()  # drop partial first line
        data = f.read()
      text = data.decode("utf-8", errors="replace")
    except OSError:
      return None
    result = self._parse(text)
    self._cache[path] = (size, result)
    return result

  def _parse(self, text):
    lines = text.splitlines()
    for raw in reversed(lines[-self.max_scan_lines:]):
      line = raw.strip()
      if not line:
        continue
      if line.startswith(_IGNORE_PREFIXES):
        continue
      m = _NINJA_RE.match(line)
      if m:
        return ("%s/%s" % (m.group(1), m.group(2)), _truncate(m.group(3)))
      m = _MAKE_PCT_RE.match(line)
      if m:
        return ("%s%%" % m.group(1), _truncate(m.group(2)))
      m = _CMAKE_INSTALL_RE.match(line)
      if m:
        return ("install", _truncate(m.group(1)))
      m = _CMAKE_DASH_RE.match(line)
      if m:
        return ("cfg", _truncate(m.group(1)))
      m = _AUTOCONF_RE.match(line)
      if m:
        return ("cfg", _truncate("checking " + m.group(1)))
    # No structured progress line; show the last non-empty raw line so
    # the user has *something* to look at during long stages.
    for raw in reversed(lines[-self.max_scan_lines:]):
      line = raw.strip()
      if not line or line.startswith(_IGNORE_PREFIXES):
        continue
      return ("…", _truncate(line))
    return None


class PipelineUI:
  """Live-updating TUI for the parallel pipeline.

  Required scheduler-side state:
    lock         : the scheduler's threading.Lock / Condition
    state_dict   : dep_name -> State enum value
    started_at   : dep_name -> monotonic timestamp when dep entered an
                   in-flight state (FETCHING / BUILDING). Updated under
                   `lock` by the scheduler.
    recent       : a bounded deque of (dep_name, terminal_state, elapsed)
                   appended to under `lock` when a dep reaches a terminal
                   state.
    state_enum   : the State enum class (so the UI can reference States by
                   name without import cycles)
  """

  def __init__(self,
               lock,
               state_dict,
               started_at,
               recent,
               state_enum,
               target_name,
               fetch_jobs,
               build_jobs,
               logdir=None,
               fetch_only_set=None):
    self.lock           = lock
    self.state_dict     = state_dict
    self.started_at     = started_at
    self.recent         = recent
    self.S              = state_enum
    self.target         = target_name
    self.fetch_jobs     = fetch_jobs
    self.build_jobs     = build_jobs
    self.logdir         = logdir
    # Names of deps in fetch-only mode (--prefetch). These reach SOURCE_READY
    # and stop — they belong in Recent, not in the Pending panel.
    self.fetch_only_set = fetch_only_set if fetch_only_set is not None else set()
    self.active         = False
    self._stop_evt      = threading.Event()
    self._thread        = None
    self._live          = None
    self._console       = None
    self._tailer        = LogTailer() if logdir is not None else None

  ############################################################################
  # Lifecycle
  ############################################################################

  def start(self):
    """Return True if the live UI is active; False otherwise (caller falls
    back to plain-text logging). On failure, prints a one-line diagnostic
    to stderr so users can tell *why* the TUI didn't engage."""
    if not _HAS_RICH:
      sys.stderr.write(
          "[ui] rich not importable — falling back to plain mode "
          "(install rich into this venv to enable the TUI)\n")
      return False
    try:
      self._console = Console()
    except Exception as e:
      sys.stderr.write("[ui] Console construction failed (%s: %s) — plain mode\n"
                       % (type(e).__name__, e))
      return False
    if not self._console.is_terminal:
      sys.stderr.write(
          "[ui] stdout is not detected as a TTY — plain mode "
          "(stdin/out/err.isatty=%s/%s/%s; TERM=%s)\n"
          % (sys.stdin.isatty(), sys.stdout.isatty(), sys.stderr.isatty(),
             os.environ.get("TERM", "<unset>")))
      return False
    self.active = True
    sys.stderr.write("[ui] TUI engaged (rich %dx%d, color=%s)\n"
                     % (self._console.width, self._console.height,
                        self._console.color_system))
    sys.stderr.flush()
    # redirect_stdout/stderr MUST be False. Rich's Live, when it owns
    # stdout/stderr, redirects them to an internal FileProxy that
    # synchronously re-renders captured output via console.print(...).
    # That render runs in the *calling* thread (i.e. the worker), and
    # the worker has obt.pipeline_io's thread-local stream pointed at
    # the per-dep log file — so Live's panels (the TUI itself) end up
    # being written into the worker's log. obt.pipeline_io already
    # routes prints/subprocess-output for us; let it do its job.
    self._live = Live(self._render(),
                      console=self._console,
                      refresh_per_second=4,
                      transient=False,
                      redirect_stdout=False,
                      redirect_stderr=False)
    self._live.__enter__()
    self._thread = threading.Thread(target=self._refresh_loop,
                                    daemon=True,
                                    name="pipeline-ui")
    self._thread.start()
    return True

  def stop(self):
    if not self.active:
      return
    self._stop_evt.set()
    if self._thread is not None:
      self._thread.join(timeout=2.0)
    if self._live is not None:
      try:
        # one final render so the panels show terminal state
        self._live.update(self._render(), refresh=True)
      except Exception:
        pass
      self._live.__exit__(None, None, None)
    self.active = False

  def _refresh_loop(self):
    while not self._stop_evt.is_set():
      try:
        self._live.update(self._render())
      except Exception:
        pass
      self._stop_evt.wait(0.25)

  ############################################################################
  # Rendering
  ############################################################################

  def _snapshot(self):
    """Pull a consistent view of the state under the scheduler lock, then
    (outside the lock) scrape each in-flight dep's log file for progress."""
    with self.lock:
      now = time.monotonic()
      counts = {}
      fetch_names = []
      pending_names = []
      build_names = []
      for name, st in self.state_dict.items():
        counts[st] = counts.get(st, 0) + 1
        if st == self.S.FETCHING:
          fetch_names.append((name, self.started_at.get(name, now)))
        elif st == self.S.SOURCE_READY:
          # Prefetched (fetch-only) deps sit at SOURCE_READY as their
          # terminal state — they're not waiting to build. Show them in
          # Recent (handled by the worker that transitions them); skip
          # them in the Pending panel.
          if name in self.fetch_only_set:
            continue
          pending_names.append((name, self.started_at.get(name, now)))
        elif st == self.S.BUILDING:
          build_names.append((name, self.started_at.get(name, now)))
      recent_rows = list(self.recent)

    # I/O happens outside the lock.
    fetch_rows = []
    for name, t0 in fetch_names:
      prog = self._progress_for(name)
      fetch_rows.append((name, now - t0, prog))
    # Pending deps have completed fetch and are waiting for a build slot
    # (or for a prereq still building). No progress label — they aren't
    # running anything yet.
    pending_rows = [(name, now - t0) for name, t0 in pending_names]
    build_rows = []
    for name, t0 in build_names:
      prog = self._progress_for(name)
      build_rows.append((name, now - t0, prog))

    fetch_rows.sort(key=lambda r: r[1], reverse=True)
    pending_rows.sort(key=lambda r: r[1], reverse=True)
    build_rows.sort(key=lambda r: r[1], reverse=True)
    return counts, fetch_rows, pending_rows, build_rows, recent_rows

  def _progress_for(self, name):
    if self._tailer is None or self.logdir is None:
      return None
    return self._tailer.scan(self.logdir / ("%s.log" % name))

  def _render(self):
    counts, fetch_rows, pending_rows, build_rows, recent_rows = self._snapshot()

    total    = sum(counts.values())
    done     = counts.get(self.S.DONE, 0)
    fetching = counts.get(self.S.FETCHING, 0)
    building = counts.get(self.S.BUILDING, 0)
    pending  = counts.get(self.S.PENDING, 0)
    src_rdy  = counts.get(self.S.SOURCE_READY, 0)
    failed   = (counts.get(self.S.FETCH_FAILED, 0)
                + counts.get(self.S.BUILD_FAILED, 0))

    # Title banner
    banner = Text()
    banner.append("OBT Pipeline ", style="bold cyan")
    banner.append("· ", style="dim")
    banner.append(self.target, style="bold yellow")
    banner.append("  ", style="dim")
    banner.append("%d/%d done" % (done, total), style="bold green")
    banner.append("  ·  ", style="dim")
    banner.append("%d pending" % pending, style="white")
    banner.append("  ·  ", style="dim")
    banner.append("%d ready" % src_rdy, style="cyan")
    if failed:
      banner.append("  ·  ", style="dim")
      banner.append("%d FAILED" % failed, style="bold red")

    # Two-axis titles: per-stage activity AND progress, so a glance at any
    # panel answers both "how busy is this stage?" and "how close to done?"
    # without having to scan back up to the banner.
    #
    # Fetch and Build have DIFFERENT denominators. In a staging-env create
    # we may fetch ~37 deps but only build ~7 (the rest are prefetch-only,
    # parking at SOURCE_READY as their terminal state). Folding fetch-only
    # deps into the Build denominator made it read "5/37 done" forever.
    #
    #   fetch_total = every dep (fetch-only deps still do fetch)
    #   build_total = only deps slated for build (excludes fetch-only)
    #   fetched     = SOURCE_READY + BUILDING + DONE (all past-fetch states)
    #   built       = DONE          (only successful builds)
    #   pending_real= deps at SOURCE_READY that are NOT fetch-only — i.e.
    #                 actually waiting to be built. Matches pending_rows.
    fetch_only_n = len(self.fetch_only_set)
    fetch_total  = total
    build_total  = total - fetch_only_n
    fetched      = src_rdy + building + done
    built        = done
    pending_real = len(pending_rows)
    fetch_title   = "Fetch   %d active   ·   %d/%d done" % (fetching, fetched, fetch_total)
    pending_title = "Pending   %d waiting" % pending_real
    build_title   = "Build   %d active   ·   %d/%d done" % (building, built, build_total)

    fetch_panel   = Panel(self._inflight_table(fetch_rows, "yellow"),
                          title=fetch_title, border_style="yellow",
                          padding=(0, 1))
    pending_panel = Panel(self._pending_table(pending_rows),
                          title=pending_title, border_style="cyan",
                          padding=(0, 1))
    build_panel   = Panel(self._inflight_table(build_rows, "green"),
                          title=build_title, border_style="green",
                          padding=(0, 1))
    recent_panel  = Panel(self._recent_table(recent_rows),
                          title="Recent", border_style="magenta",
                          padding=(0, 1))

    return Group(banner, fetch_panel, pending_panel, build_panel, recent_panel)

  def _pending_table(self, rows):
    """Deps that have completed fetch and are waiting for a build slot or
    for unfinished prereqs. Names only — no timer needed; they're idle."""
    if not rows:
      return Text("(none)", style="dim")
    items = [Text(name, style="cyan") for name, _waiting in rows]
    return Columns(items, expand=True, equal=True, padding=(0, 2))

  def _inflight_table(self, rows, color):
    t = Table.grid(padding=(0, 2), expand=False)
    t.add_column(style=color, no_wrap=True)         # dep name
    t.add_column(justify="right", style="white", no_wrap=True)  # elapsed
    t.add_column(justify="right", style="magenta", no_wrap=True)  # progress label
    t.add_column(style="dim", no_wrap=True)         # activity
    if not rows:
      t.add_row(Text("(idle)", style="dim"), "", "", "")
    else:
      for name, elapsed, prog in rows:
        if prog is None:
          label, activity = "", ""
        else:
          label, activity = prog
        t.add_row(name, _fmt_elapsed(elapsed), label, activity)
    return t

  def _recent_table(self, rows):
    """Recent panel body. Lays out items in multiple columns so the panel
    doesn't grow tall on long runs. Newest first (most recent terminal
    transition is top-left)."""
    if not rows:
      return Text("(none yet)", style="dim")
    items = []
    for name, state, elapsed in reversed(rows):
      txt = Text()
      if state == self.S.DONE:
        txt.append("✓ ", style="bold green")
        txt.append(name, style="white")
      elif state == self.S.SOURCE_READY:
        txt.append("◉ ", style="bold cyan")
        txt.append(name, style="white")
      elif state in (self.S.FETCH_FAILED, self.S.BUILD_FAILED):
        txt.append("✗ ", style="bold red")
        txt.append(name, style="red")
      else:
        txt.append("· ", style="dim")
        txt.append(name, style="dim")
      txt.append("  ")
      txt.append(_fmt_elapsed(elapsed), style="dim")
      items.append(txt)
    return Columns(items, expand=True, equal=True, padding=(0, 2))


###############################################################################
# Stub UI for plain mode / no TTY / no rich
###############################################################################

class StubUI:
  """No-op UI. start() returns False so the scheduler uses its own
  print()-based status output."""
  def __init__(self, *args, **kwargs):
    self.active = False
  def start(self):
    return False
  def stop(self):
    pass
