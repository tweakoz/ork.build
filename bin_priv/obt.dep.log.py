#!/usr/bin/env python3
###############################################################################
# Orkid Build Tools
# obt.dep.log.py
#
# View build logs produced by obt.dep.pipeline.py.
#
# Logs live at $OBT_STAGE/.pipeline-logs/<dep>.log and contain captured
# stdout+stderr (including subprocess output) from each fetch / build /
# install run.
###############################################################################

import os
import re
import sys
import argparse
import time
from pathlib import Path


###############################################################################
# TUI noise filter
#
# Today, the rich Live renderer occasionally leaks into per-dep log files
# (root cause still under investigation). Until that's fixed at the source,
# strip ANSI escape sequences and drop lines that are clearly TUI banner /
# panel-border content so the viewer shows clean build output by default.
###############################################################################

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_BOX_DRAW = set("│╭╰─├┤┬┴┼")

_TUI_HINTS = (
    "OBT Pipeline",
    "Fetch  ",       # "Fetch  3 / 8" panel title
    "Build  ",       # "Build  4 / 8" panel title
    "(idle)",
    "(none yet)",
    " pending",
    " ready",
    " in flight",
    " FAILED",       # banner suffix, distinct from real failure lines
)


def _is_tui_line(text):
  """Return True if a line (already ANSI-stripped) looks like TUI content."""
  s = text.lstrip()
  if not s:
    return False
  if s[0] in _BOX_DRAW:
    return True
  # Some panel rows have an ANSI-stripped form like "boost  2m 13s   42%  ..."
  # — those we keep (they're the build's actual recent activity). Only drop
  # the obvious banner / panel-title lines.
  for hint in _TUI_HINTS:
    if hint in s:
      return True
  return False


def strip_tui(text):
  """Strip ANSI escape codes and drop TUI banner/panel lines."""
  clean = _ANSI_RE.sub("", text)
  lines = clean.splitlines()
  out = []
  for line in lines:
    if _is_tui_line(line):
      continue
    out.append(line)
  return "\n".join(out)


def find_logroot():
  """Root of pipeline logs. Each pipeline run lives under logroot/<jobid>/."""
  obt_stage = os.environ.get("OBT_STAGE")
  if obt_stage:
    return Path(obt_stage) / ".pipeline-logs"
  return Path("/tmp") / "obt-pipeline-logs"


def list_jobids(logroot):
  """All <jobid>/ subdirs, lex-sorted (which is also time-sorted because
  jobids are hex unix timestamps). Oldest first."""
  if not logroot.exists():
    return []
  out = []
  for p in logroot.iterdir():
    if not p.is_dir() or p.is_symlink():
      continue
    out.append(p)
  out.sort(key=lambda p: p.name)
  return out


def latest_jobid(logroot):
  """Find the latest jobid. Prefer the 'latest' symlink (set by the
  pipeline at startup); fall back to lex-sorting jobid dirs."""
  latest = logroot / "latest"
  if latest.is_symlink():
    target_name = os.readlink(latest)
    target = logroot / target_name
    if target.is_dir():
      return target.name
  jobs = list_jobids(logroot)
  return jobs[-1].name if jobs else None


def resolve_logdir(logroot, jobid):
  """Return logroot/<jobid>, or None if it doesn't exist."""
  if jobid is None:
    jobid = latest_jobid(logroot)
    if jobid is None:
      return None
  d = logroot / jobid
  return d if d.is_dir() else None


def list_jobs(logroot):
  """Print all known job runs."""
  jobs = list_jobids(logroot)
  if not jobs:
    print("(no jobs in %s)" % logroot)
    return 0
  current_latest = latest_jobid(logroot)
  print("%-18s %-22s %6s  %s" % ("jobid", "started", "deps", ""))
  print("-" * 60)
  for jobdir in jobs:
    jid = jobdir.name
    try:
      ts = int(jid, 16)
      started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except ValueError:
      started = "?"
    count = sum(1 for _ in jobdir.glob("*.log"))
    marker = "← latest" if jid == current_latest else ""
    print("%-18s %-22s %6d  %s" % (jid, started, count, marker))
  return 0


def list_logs(logdir):
  if logdir is None or not logdir.exists():
    print("(no log directory)")
    return 0
  logs = sorted(logdir.glob("*.log"))
  if not logs:
    print("(no logs in %s)" % logdir)
    return 0
  print("# logs in %s" % logdir)
  print("%-30s %10s  %s" % ("dep", "size", "modified"))
  print("-" * 70)
  for p in logs:
    st = p.stat()
    if st.st_size >= 1024 * 1024:
      size_s = "%.1f MB" % (st.st_size / (1024 * 1024))
    elif st.st_size >= 1024:
      size_s = "%.1f KB" % (st.st_size / 1024)
    else:
      size_s = "%d B" % st.st_size
    mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
    print("%-30s %10s  %s" % (p.stem, size_s, mtime))
  return 0


def show(path, tail=None, head=None, raw=False):
  if not path.exists():
    print("log not found: %s" % path, file=sys.stderr)
    return 1
  try:
    text = path.read_text(errors="replace")
  except Exception as e:
    print("error reading %s: %s" % (path, e), file=sys.stderr)
    return 1
  if not raw:
    text = strip_tui(text)
  if tail is not None:
    lines = text.splitlines()
    sys.stdout.write("\n".join(lines[-tail:]))
    sys.stdout.write("\n")
  elif head is not None:
    lines = text.splitlines()
    sys.stdout.write("\n".join(lines[:head]))
    sys.stdout.write("\n")
  else:
    sys.stdout.write(text)
    if not text.endswith("\n"):
      sys.stdout.write("\n")
  return 0


def follow(path, raw=False):
  """Tail -f a log. Polls every 250ms. Handles file-not-yet-existing by
  waiting until it appears."""
  print("[follow] %s" % path, file=sys.stderr)
  while not path.exists():
    try:
      time.sleep(0.25)
    except KeyboardInterrupt:
      return 0
  buf = ""
  def emit_buffered():
    nonlocal buf
    if not buf:
      return
    out = buf if raw else strip_tui(buf)
    sys.stdout.write(out)
    if out and not out.endswith("\n"):
      sys.stdout.write("\n")
    sys.stdout.flush()
    buf = ""
  try:
    with open(path, "r", errors="replace") as f:
      # show what's already there, filtered
      head = f.read()
      sys.stdout.write(head if raw else strip_tui(head))
      sys.stdout.flush()
      while True:
        line = f.readline()
        if not line:
          emit_buffered()
          time.sleep(0.25)
          continue
        if raw:
          sys.stdout.write(line)
          sys.stdout.flush()
        else:
          buf += line
          if line.endswith("\n"):
            emit_buffered()
  except KeyboardInterrupt:
    return 0
  return 0


def main():
  ap = argparse.ArgumentParser(
      description="View OBT pipeline build logs (from obt.dep.pipeline.py). "
                  "Logs are organized as $OBT_STAGE/.pipeline-logs/<jobid>/<dep>.log; "
                  "by default the latest jobid is used.")
  ap.add_argument("dep", nargs="?",
      help="dep name (omit with --list / --list-jobs)")
  ap.add_argument("--jobid", default=None, metavar="HEX",
      help="specific run to view (default: latest). See --list-jobs.")
  ap.add_argument("--list", action="store_true",
      help="list all dep logs in the selected jobid")
  ap.add_argument("--list-jobs", action="store_true",
      help="list all known pipeline runs (jobids) and exit")
  ap.add_argument("--tail", type=int, default=None, metavar="N",
      help="show only the last N lines")
  ap.add_argument("--head", type=int, default=None, metavar="N",
      help="show only the first N lines")
  ap.add_argument("--follow", "-f", action="store_true",
      help="tail -f the log (Ctrl-C to exit)")
  ap.add_argument("--print-path", action="store_true",
      help="print the log file path and exit (useful for piping)")
  ap.add_argument("--raw", action="store_true",
      help="show raw content (default strips ANSI escapes and TUI noise)")
  args = ap.parse_args()

  logroot = find_logroot()

  if args.list_jobs:
    return list_jobs(logroot)

  logdir = resolve_logdir(logroot, args.jobid)
  if logdir is None:
    if args.jobid:
      print("jobid not found: %s" % args.jobid, file=sys.stderr)
      print("Try: obt.dep.log.py --list-jobs", file=sys.stderr)
    else:
      print("no pipeline runs found under %s" % logroot, file=sys.stderr)
    return 1

  if args.list:
    return list_logs(logdir)

  if not args.dep:
    ap.print_usage()
    print("\nTry: obt.dep.log.py --list", file=sys.stderr)
    print("Try: obt.dep.log.py --list-jobs", file=sys.stderr)
    return 2

  path = logdir / ("%s.log" % args.dep)

  if args.print_path:
    print(path)
    return 0 if path.exists() else 1

  if args.follow:
    return follow(path, raw=args.raw)

  return show(path, tail=args.tail, head=args.head, raw=args.raw)


if __name__ == "__main__":
  sys.exit(main())
