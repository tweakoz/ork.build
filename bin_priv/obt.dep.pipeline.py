#!/usr/bin/env python3
###############################################################################
# Orkid Build Tools
# obt.dep.pipeline.py
#
# Concurrent dep build pipeline.
#
# Walks the dep DAG once, fetches sources concurrently in a fetch worker pool,
# and builds deps concurrently in a build worker pool. The two pools overlap
# in time: a leaf dep with a fast wget tarball can be DONE while deeper deps
# are still fetching. A build only starts when its own source is ready AND
# all of its prerequisites are DONE.
#
# A fetch failure (after retries) does NOT abort the pipeline — other
# independent subtrees keep going. The pipeline halts the first time a build
# worker tries to start a dep with a failed transitive prerequisite.
#
# See ~/OBTPARALLEL.md for full design notes.
###############################################################################

import os
import sys
import argparse
import threading
import multiprocessing
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path

import obt._globals
from obt import pipeline_io, pipeline_ui


###############################################################################
# State machine
###############################################################################

class State(Enum):
  PENDING       = "PENDING"
  FETCHING      = "FETCHING"
  SOURCE_READY  = "SOURCE_READY"
  FETCH_FAILED  = "FETCH_FAILED"
  BUILDING      = "BUILDING"
  DONE          = "DONE"
  BUILD_FAILED  = "BUILD_FAILED"


_TERMINAL = {State.DONE, State.FETCH_FAILED, State.BUILD_FAILED}


###############################################################################
# Scheduler state (process-global; single-process scheduler)
###############################################################################

_lock          = threading.RLock()
_cond          = threading.Condition(_lock)
_state         = {}                  # dep_name -> State
_providers     = {}                  # dep_name -> Provider
_started_at    = {}                  # dep_name -> monotonic ts of in-flight entry
_recent        = deque(maxlen=20)    # (name, terminal_state, elapsed) tuples
_fetch_only_set = set()              # dep names whose role is "fetch only, no build"
_halt          = [False]
_ui_active     = [False]             # set True when rich TUI is up
_logdir        = [None]              # set in main() once OBT_STAGE is known


def _log_path(name, stage):
  """Per-dep log file path. Combines fetch + build output into one file so
  obt.dep.log.py can show the full lifecycle without juggling two files."""
  return _logdir[0] / ("%s.log" % name)


def _quiet_print(*args, **kwargs):
  """print() that no-ops when the rich UI owns the terminal. Use for
  scheduler-level status lines. Worker logs go to per-dep files via the
  pipeline_io redirect, so they're never quieted."""
  if _ui_active[0]:
    return
  print(*args, **kwargs)


# The DAG itself encodes the correct build ordering for the bootstrap deps
# (root → pydefaults → python → {xz, openssl}). The cycle-break in
# scripts/obt/_dep_provider.py:22 (root_dep_list) is a *dep instance init*
# concern, not a build-ordering one. pydefaults is the only one with
# concurrency concerns (it calls pip.install), and that's handled by the
# module-level lock in scripts/obt/pip.py.
ROOT_DEP_PRELUDE = []


###############################################################################
# Helpers
###############################################################################

def _prereqs_done(provider):
  for inst in provider._required_deps.values():
    if inst is None:
      continue
    if _state.get(inst._name) != State.DONE:
      return False
  return True


def _any_prereq_failed(provider):
  for inst in provider._required_deps.values():
    if inst is None:
      continue
    if _state.get(inst._name) in (State.FETCH_FAILED, State.BUILD_FAILED):
      return True
  return False


def _all_done():
  return all(s in _TERMINAL for s in _state.values())


def _state_counts():
  counts = {}
  for s in _state.values():
    counts[s.name] = counts.get(s.name, 0) + 1
  return counts


def _print_state_summary(prefix=""):
  c = _state_counts()
  parts = ["%s=%d" % (k, v) for k, v in sorted(c.items())]
  print("%sstate: %s" % (prefix, ", ".join(parts)))


###############################################################################
# Worker bodies
###############################################################################

def _do_fetch(provider):
  name = provider._name
  _quiet_print("  [fetch] %s : starting" % name)
  logpath = _log_path(name, _logdir[0])
  ok = False
  with pipeline_io.redirect_thread_io(logpath):
    print("=" * 60)
    print("FETCH %s (%s)" % (name, time.strftime("%Y-%m-%d %H:%M:%S")))
    print("=" * 60)
    try:
      ok = bool(provider.fetch_only())
    except Exception as e:
      print("[fetch] %s raised %s: %s" % (name, type(e).__name__, e))
      ok = False
    print("[fetch] %s -> %s" % (name, "OK" if ok else "FAIL"))
  with _cond:
    new_state = State.SOURCE_READY if ok else State.FETCH_FAILED
    elapsed = time.monotonic() - _started_at.get(name, time.monotonic())
    _state[name] = new_state
    if new_state == State.SOURCE_READY:
      # Reset the timer so the Pending panel can show "waiting since fetch
      # completed" — it's updated again to "build start" on the next
      # transition.
      _started_at[name] = time.monotonic()
      # Prefetched deps terminate here (they never build). Surface them
      # in the Recent panel; the TUI's Pending panel filters them out.
      if name in _fetch_only_set:
        _recent.append((name, new_state, elapsed))
    if new_state == State.FETCH_FAILED:
      _recent.append((name, new_state, elapsed))
    _cond.notify_all()
  _quiet_print("  [fetch] %s : %s" % (name, new_state.name))


def _do_build(provider):
  name = provider._name
  _quiet_print("  [build] %s : starting" % name)
  logpath = _log_path(name, _logdir[0])
  ok = False
  with pipeline_io.redirect_thread_io(logpath):
    print("=" * 60)
    print("BUILD %s (%s)" % (name, time.strftime("%Y-%m-%d %H:%M:%S")))
    print("=" * 60)
    try:
      ok = bool(provider.build_and_install())
    except Exception as e:
      print("[build] %s raised %s: %s" % (name, type(e).__name__, e))
      ok = False
    print("[build] %s -> %s" % (name, "OK" if ok else "FAIL"))
  with _cond:
    new_state = State.DONE if ok else State.BUILD_FAILED
    elapsed = time.monotonic() - _started_at.get(name, time.monotonic())
    _state[name] = new_state
    _recent.append((name, new_state, elapsed))
    _cond.notify_all()
  _quiet_print("  [build] %s : %s" % (name, new_state.name))


###############################################################################
# Phase 1 — Plan
###############################################################################

def phase1_plan(build_targets, prefetch_targets=None):
  """Build the Chain, seed state from manifests, return ordered dep list.

  build_targets    : list of dep names to fetch AND build (and all transitives)
  prefetch_targets : list of dep names to fetch but NOT build (and all
                     transitives). Deps that appear in BOTH a build target's
                     chain and a prefetch target's chain are classified as
                     build (build wins — a transitive of something we need
                     to build is itself built).

  Deps already provisioned (manifest exists, not forcing rebuild) are
  pre-marked DONE. Deps that don't support this host are also marked DONE
  (no-op). The remainder start as PENDING.

  Side effect: populates _fetch_only_set with dep names whose role is
  fetch-only. The dispatch loop and termination logic check this set.
  """
  from obt import dep
  if isinstance(build_targets, str):
    build_targets = [build_targets]
  prefetch_targets = list(prefetch_targets or [])

  all_targets = list(build_targets) + prefetch_targets
  chain = dep.Chain(all_targets)
  deps = list(reversed(chain._list))   # dependencies-first order

  # Compute the set of dep names reachable from any build_target's chain.
  # Anything in the overall chain NOT in that set is fetch-only (it only
  # got pulled in because it's in a prefetch_target's chain).
  build_reachable = set()
  for t in build_targets:
    sub = dep.Chain(t)
    for p in sub._list:
      build_reachable.add(p._name)

  with _cond:
    _fetch_only_set.clear()
    for p in deps:
      _providers[p._name] = p
      if p._name not in build_reachable:
        _fetch_only_set.add(p._name)
      if not p.supports_host:
        _state[p._name] = State.DONE
        continue
      # If the manifest is in place and the user isn't forcing a rebuild,
      # treat the dep as already provisioned. This mirrors the existing
      # serial path's `should_build` short-circuit.
      if p.OK and not p.should_force_build and not p.should_wipe:
        _state[p._name] = State.DONE
      else:
        _state[p._name] = State.PENDING
  return deps


def print_plan(deps):
  fetcher_count = {}
  pending = 0
  done = 0
  for p in deps:
    if _state[p._name] == State.DONE:
      done += 1
      continue
    pending += 1
    ftype = "NoFetcher"
    fobj = getattr(p, "_fetcher", None)
    if fobj is not None:
      ftype = type(fobj).__name__
    fetcher_count[ftype] = fetcher_count.get(ftype, 0) + 1
  print("=" * 60)
  print("PIPELINE PLAN")
  print("=" * 60)
  print("  total deps:          %d" % len(deps))
  print("  already provisioned: %d" % done)
  print("  to process:          %d" % pending)
  if fetcher_count:
    print("  fetcher breakdown:")
    for k in sorted(fetcher_count.keys()):
      print("    %-20s %d" % (k, fetcher_count[k]))
  print("=" * 60)


###############################################################################
# Phase 2 — Serial prelude + concurrent overlapped fetch/build
###############################################################################

def serial_prelude(deps):
  """Build ROOT_DEP_PRELUDE members one at a time, in order. Required to
  break the bootstrap dep cycle before the parallel phase unlocks."""
  name_to_provider = {p._name: p for p in deps}
  for name in ROOT_DEP_PRELUDE:
    p = name_to_provider.get(name)
    if p is None:
      continue
    if _state.get(name) == State.DONE:
      _quiet_print("  [prelude] %s : already done" % name)
      continue
    _quiet_print("  [prelude] %s : building (serial)" % name)
    with _cond:
      _state[name] = State.BUILDING
      _started_at[name] = time.monotonic()
    logpath = _log_path(name, _logdir[0])
    ok = False
    with pipeline_io.redirect_thread_io(logpath):
      print("=" * 60)
      print("PRELUDE %s (%s)" % (name, time.strftime("%Y-%m-%d %H:%M:%S")))
      print("=" * 60)
      try:
        ok = bool(p.provide())
      except Exception as e:
        print("[prelude] %s raised %s: %s" % (name, type(e).__name__, e))
        ok = False
    with _cond:
      elapsed = time.monotonic() - _started_at.get(name, time.monotonic())
      _state[name] = State.DONE if ok else State.BUILD_FAILED
      _recent.append((name, _state[name], elapsed))
      _cond.notify_all()
    if not ok:
      _quiet_print("  [prelude] %s : FAILED — aborting pipeline" % name)
      return False
  return True


def _dispatch_loop(deps, fetch_pool, build_pool,
                   fetch_jobs, build_jobs,
                   fetch_only=False):
  """Main scheduler loop. Dispatches fetches and builds as state advances.
  Returns when all deps are in terminal states OR _halt is set.

  In fetch_only mode the build pool is never used, and SOURCE_READY counts
  as a terminal-success state for the purpose of termination. Per-dep
  fetch-only (from _fetch_only_set / --prefetch) is checked at dispatch
  time and in the per-dep termination predicate below."""

  def _is_terminal(name, state):
    if state in _TERMINAL:
      return True
    if state == State.SOURCE_READY:
      if fetch_only:
        return True
      if name in _fetch_only_set:
        return True
    return False

  while True:
    to_fetch = []
    to_build = []
    with _cond:
      if _halt[0]:
        return

      n_fetching = sum(1 for s in _state.values() if s == State.FETCHING)
      n_building = sum(1 for s in _state.values() if s == State.BUILDING)

      # ---- fetch dispatch ----
      fetch_avail = max(0, fetch_jobs - n_fetching)
      if fetch_avail > 0:
        for p in deps:
          if len(to_fetch) >= fetch_avail:
            break
          if _state.get(p._name) != State.PENDING:
            continue
          if p.serial_fetch and n_fetching > 0:
            continue
          to_fetch.append(p)
          _state[p._name] = State.FETCHING
          _started_at[p._name] = time.monotonic()
          n_fetching += 1
          if p.serial_fetch:
            break

      # ---- build dispatch (skipped in fetch_only mode) ----
      if not fetch_only:
        build_avail = max(0, build_jobs - n_building)
        if build_avail > 0:
          for p in deps:
            if len(to_build) >= build_avail:
              break
            if _state.get(p._name) != State.SOURCE_READY:
              continue
            # Per-dep fetch-only marker (from --prefetch). These deps stop
            # at SOURCE_READY and never enter the build queue.
            if p._name in _fetch_only_set:
              continue
            if not _prereqs_done(p):
              if _any_prereq_failed(p):
                # Cascade the failure: this dep can never build. Mark it
                # BUILD_FAILED so the failure propagates to its own
                # dependents on the next loop tick, but DO NOT halt the
                # scheduler — independent subgraphs should still complete.
                # Halting on first failure left unrelated deps stuck at
                # SOURCE_READY forever (see: cpppeglib failure that froze
                # 13 unrelated pendings).
                _quiet_print("[scheduler] %s : blocked by failed prereq"
                             % p._name)
                _state[p._name] = State.BUILD_FAILED
                _recent.append((p._name, State.BUILD_FAILED, 0))
              continue
            if p.serial_build and n_building > 0:
              continue
            to_build.append(p)
            _state[p._name] = State.BUILDING
            _started_at[p._name] = time.monotonic()
            n_building += 1
            if p.serial_build:
              break

      if _halt[0]:
        continue

      # Termination checks. _is_terminal handles both global fetch_only
      # mode and per-dep fetch-only (from _fetch_only_set).
      if all(_is_terminal(n, s) for n, s in _state.items()):
        return
      if (not to_fetch and not to_build
          and n_fetching == 0 and n_building == 0):
        stuck = [n for n, s in _state.items() if not _is_terminal(n, s)]
        if stuck:
          print("[scheduler] no path forward — stuck deps: %s" % sorted(stuck))
          for n in stuck:
            _state[n] = State.BUILD_FAILED
        return

    for p in to_fetch:
      fetch_pool.submit(_do_fetch, p)
    for p in to_build:
      build_pool.submit(_do_build, p)

    with _cond:
      _cond.wait(timeout=1.0)


def phase2_execute(deps, fetch_jobs, build_jobs, fetch_only=False):
  if fetch_only:
    _quiet_print("[scheduler] fetch-only mode : skipping serial prelude")
  else:
    _quiet_print("[scheduler] serial prelude")
    if not serial_prelude(deps):
      return False
  _quiet_print("[scheduler] parallel phase : fetch_jobs=%d build_jobs=%d%s"
               % (fetch_jobs, build_jobs,
                  " (fetch-only)" if fetch_only else ""))
  with ThreadPoolExecutor(max_workers=fetch_jobs) as fetch_pool, \
       ThreadPoolExecutor(max_workers=build_jobs) as build_pool:
    _dispatch_loop(deps, fetch_pool, build_pool,
                   fetch_jobs, build_jobs,
                   fetch_only=fetch_only)
  if fetch_only:
    ok_states = {State.SOURCE_READY, State.DONE}
    return all(_state.get(p._name) in ok_states
               for p in deps if p.supports_host)
  return all(_state.get(p._name) == State.DONE
             for p in deps if p.supports_host)


###############################################################################
# Serial fallback (--serial)
###############################################################################

def run_serial(deps, fetch_only=False):
  """Single-threaded whole-pipeline serial mode. One thing at a time,
  no overlap. Matches the existing bin_priv/obt.dep.build.py behavior,
  with per-dep log capture so the TUI / log viewer still work."""
  for p in deps:
    if not p.supports_host:
      continue
    name = p._name

    # Decide what stage to run for this dep.
    if fetch_only:
      stage = "fetch"
      with _cond:
        _state[name] = State.FETCHING
        _started_at[name] = time.monotonic()
    else:
      if not p.should_build:
        with _cond:
          if _state.get(name) != State.DONE:
            _state[name] = State.DONE
        continue
      stage = "build"
      with _cond:
        _state[name] = State.BUILDING
        _started_at[name] = time.monotonic()

    logpath = _log_path(name, _logdir[0])
    ok = False
    with pipeline_io.redirect_thread_io(logpath):
      print("=" * 60)
      print("SERIAL %s %s (%s)"
            % (stage.upper(), name, time.strftime("%Y-%m-%d %H:%M:%S")))
      print("=" * 60)
      try:
        if fetch_only:
          ok = bool(p.fetch_only())
        else:
          ok = bool(p.provide())
      except Exception as e:
        print("[%s] %s raised %s: %s"
              % (stage, name, type(e).__name__, e))
        ok = False

    with _cond:
      elapsed = time.monotonic() - _started_at.get(name, time.monotonic())
      if fetch_only:
        new_state = State.SOURCE_READY if ok else State.FETCH_FAILED
      else:
        new_state = State.DONE if ok else State.BUILD_FAILED
      _state[name] = new_state
      _recent.append((name, new_state, elapsed))
      _cond.notify_all()

    if not ok:
      return False
  return True


###############################################################################
# Main
###############################################################################

def main():
  parser = argparse.ArgumentParser(
      description="OBT concurrent dep build pipeline. "
                  "See ~/OBTPARALLEL.md for design.")
  parser.add_argument("dependency", type=str, nargs="+",
      help="root dep(s) to build (full dep tree is included for each; the "
           "union is scheduled as one DAG)")
  parser.add_argument("--force",       action="store_true", help="force rebuild")
  parser.add_argument("--wipe",        action="store_true", help="wipe and refetch")
  parser.add_argument("--nofetch",     action="store_true",
      help="skip fetch step (assume source already present)")
  parser.add_argument("--incremental", action="store_true", help="incremental rebuild")
  parser.add_argument("--serial",      action="store_true",
      help="whole-pipeline serial: one thing at a time, no overlap, intra-dep -j1")
  parser.add_argument("--usegitclone", action="store_true",
      help="use git clone for github deps instead of wget tarball")
  parser.add_argument("--verbose",     action="store_true", help="verbose build")
  parser.add_argument("--debug",       action="store_true", help="debug build")
  parser.add_argument("--dry-run",     action="store_true",
      help="phase 1 only: print plan and exit without running any work")
  parser.add_argument("--fetch-jobs",  type=int, default=None,
      help="fetch pool size (default $OBT_FETCH_JOBS or 8)")
  parser.add_argument("--build-jobs",  type=int, default=None,
      help="build pool size (default $OBT_BUILD_JOBS or 8)")
  parser.add_argument("--fetch-only",  dest="fetch_only", action="store_true",
      help="fetch source for the dep and all transitive prereqs concurrently; "
           "skip serial prelude and build entirely")
  parser.add_argument("--prefetch", default=None, metavar="DEPS",
      help="comma-separated dep names whose source should be fetched but NOT "
           "built (their transitive prereqs are also fetch-only unless they're "
           "in a build target's chain). Useful with --pipeline during "
           "obt.env.create.py to pre-warm the source cache while the bootstrap "
           "builds.")
  parser.add_argument("--ui", choices=["rich", "plain", "auto"], default="auto",
      help="UI mode: 'rich' (live TUI), 'plain' (line-by-line), or 'auto' "
           "(rich when stdout is a TTY, plain otherwise)")
  args = parser.parse_args()

  # Resolve job counts.
  numcores = multiprocessing.cpu_count()
  fetch_jobs = (args.fetch_jobs
                if args.fetch_jobs is not None
                else int(os.environ.get("OBT_FETCH_JOBS", "8")))
  build_jobs = (args.build_jobs
                if args.build_jobs is not None
                else int(os.environ.get("OBT_BUILD_JOBS", "8")))
  if args.serial:
    fetch_jobs = 1
    build_jobs = 1

  # Set the OBT globals that should_build / should_wipe / etc. read.
  # depname is used by is_primary_dep; for multi-target we use the first
  # name (--force/--wipe/--incremental only apply meaningfully to a single
  # primary anyway).
  obt._globals.setOption("depname", args.dependency[0])
  for k in "force wipe incremental nofetch serial usegitclone verbose debug".split():
    obt._globals.setOption(k, getattr(args, k) is True)

  # Subspace guard — mirrors bin_priv/obt.dep.build.py, applied to each
  # requested target.
  if os.environ.get("OBT_SUBSPACE", "host") != "host":
    from obt import dep
    for depname in args.dependency:
      node = dep.instance(depname)
      if node is None or not node._allow_build_in_subspaces:
        print("Dependency %s not allowed to be built in subspaces other than host"
              % depname)
        sys.exit(-1)

  # Resolve and create a per-run log directory. Each pipeline invocation
  # gets its own <jobid>/ subdir so logs don't accumulate across runs.
  # jobid is a hex-encoded unix timestamp — lex-sortable, human-decodable.
  obt_stage = os.environ.get("OBT_STAGE")
  if obt_stage:
    logroot = Path(obt_stage) / ".pipeline-logs"
  else:
    logroot = Path("/tmp") / "obt-pipeline-logs"
  jobid = "%016x" % int(time.time())
  _logdir[0] = logroot / jobid
  _logdir[0].mkdir(parents=True, exist_ok=True)

  # Refresh the 'latest' pointer for obt.dep.log.py's default lookup.
  latest = logroot / "latest"
  try:
    if latest.is_symlink() or latest.exists():
      latest.unlink()
    latest.symlink_to(jobid)
  except OSError:
    pass

  print("[pipeline] jobid: %s" % jobid)
  print("[pipeline] logs:  %s" % _logdir[0])

  # Install per-thread stdout/stderr capture so worker output goes to the
  # dep's log file rather than the terminal.
  pipeline_io.install()

  prefetch_targets = []
  if args.prefetch:
    prefetch_targets = [d.strip() for d in args.prefetch.split(",") if d.strip()]

  deps = phase1_plan(args.dependency, prefetch_targets=prefetch_targets)
  print_plan(deps)
  if prefetch_targets:
    n_fo = len([p for p in deps if p._name in _fetch_only_set])
    print("[plan] prefetch targets: %s  (%d fetch-only deps total)"
          % (",".join(prefetch_targets), n_fo))

  if args.dry_run:
    print("[dry-run] exiting after plan")
    sys.exit(0)

  # Decide UI mode. Serial mode also gets the TUI if --ui rich or auto-tty.
  want_rich = (args.ui == "rich") or (args.ui == "auto")
  ui = None
  if want_rich:
    ui = pipeline_ui.PipelineUI(
        lock=_lock,
        state_dict=_state,
        started_at=_started_at,
        recent=_recent,
        state_enum=State,
        target_name=" ".join(args.dependency),
        fetch_jobs=fetch_jobs,
        build_jobs=build_jobs,
        logdir=_logdir[0],
        fetch_only_set=_fetch_only_set)
    if ui.start():
      _ui_active[0] = True
    else:
      ui = None

  ok = False
  try:
    if args.serial:
      _quiet_print("[mode] serial%s" % (" fetch-only" if args.fetch_only else ""))
      ok = run_serial(deps, fetch_only=args.fetch_only)
    else:
      ok = phase2_execute(deps, fetch_jobs, build_jobs,
                          fetch_only=args.fetch_only)
  finally:
    if ui is not None:
      ui.stop()
    _ui_active[0] = False

  # Final summary (after UI is down).
  print("=" * 60)
  print("PIPELINE SUMMARY")
  print("=" * 60)
  _print_state_summary(prefix="  ")
  failed = sorted(n for n, s in _state.items()
                  if s in (State.FETCH_FAILED, State.BUILD_FAILED))
  if failed:
    print("FAILED:")
    for n in failed:
      print("  %-30s %s   log: %s"
            % (n, _state[n].name, _log_path(n, _logdir[0])))
  print("logs: %s" % _logdir[0])
  sys.exit(0 if ok else 1)


if __name__ == "__main__":
  main()
