#!/usr/bin/env python3
###############################################################################
# Orkid Build Tools
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# obt.test.nohomebrew.py
#
# Bootstrap an OBT staging from scratch under a sanitized environment, then
# verify zero homebrew leakage in the result. The bootstrap python (host
# /opt/homebrew/bin/python3 used to seed the venv) is the only allowed brew
# reference; everything else is treated as a leak.
#
# Pipeline (default mode):
#   1. wipe <root>/
#   2. <bootstrap-python> -m venv <root>/venv
#   3. <root>/venv/bin/pip install --upgrade --force-reinstall <ork.build repo>
#   4. <root>/venv/bin/obt.env.create.py --stagedir <root>/staging
#   5. scan <root>/venv and <root>/staging for /opt/homebrew references
#
# Every subprocess runs under a freshly-built env dict (no inheritance from
# whatever shell invoked us), so a parent OBT shell cannot leak in.
###############################################################################

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Brew references containing "python" (the bootstrap python we explicitly allow).
# Anything else under /opt/homebrew is a leak.
HOMEBREW_RE = re.compile(r"/opt/homebrew/[^\s'\")(:]+")
ALLOWED_RE  = re.compile(r"/opt/homebrew/[^\s'\")(:]*python[^\s'\")(:]*", re.IGNORECASE)

MACHO_MAGICS = {
    b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",  # 64-bit
    b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce",  # 32-bit
    b"\xca\xfe\xba\xbe",                        # fat
}

TEXT_EXTS = (".cfg", ".cmake", ".pc", ".sh", ".rc", ".la", ".conf", ".ini")
# .py is intentionally excluded: dep-provider source files may legitimately
# reference brew paths for deps that aren't actually consumed by the
# bootstrap (e.g. qt5.py, realsense2.py). The artifact-level scan catches
# anything that actually gets built and linked.


def hdr(s):  print(f"\n=== {s} ===")
def info(s): print(f"   {s}")
def warn(s): print(f"!! {s}", file=sys.stderr)
def die(s, code=1):
    warn(s)
    sys.exit(code)


def safe_wipe(root: Path, repo: Path):
    """Refuse to wipe anything that could cost real work.

    Rules:
      - root must have >= 3 path components (no /tmp, /Users, etc.)
      - root must not EQUAL HOME, repo, OBT_STAGE, or OBT_VENV_DIR
      - root must not be an ANCESTOR of any of those (would delete them)
    """
    real = root.resolve()
    if len(real.parts) < 3:
        die(f"refusing to wipe {root}: path too shallow ({real})")
    protected = [Path.home().resolve(), repo.resolve()]
    for var in ("OBT_STAGE", "OBT_VENV_DIR", "OBT_PYTHONHOME"):
        v = os.environ.get(var)
        if v:
            try:
                protected.append(Path(v).resolve())
            except Exception:
                pass
    for f in protected:
        if real == f:
            die(f"refusing to wipe {root}: equals protected path {f}")
        try:
            f.relative_to(real)  # f is under real → real would delete f
            die(f"refusing to wipe {root}: would delete protected path {f}")
        except ValueError:
            pass
    if real.exists():
        info(f"wiping {root}")
        shutil.rmtree(real)


def sanitized_env(venv_bin: Path = None, extras=None) -> dict:
    """Build a fresh env dict with zero parent-shell carryover.

    Policy: brew CLI tools (wget, perl, ...) on PATH are OK because the
    artifact-level scan is the authoritative gate. The test venv's bin is
    listed FIRST so the venv's python/pip win over any brew shadow.

    When venv_bin is given, also set VIRTUAL_ENV (normally set by `activate`)
    so OBT's _obt_config.py can resolve the venv's site-packages without
    falling back to site.getsitepackages() (which a homebrew sitecustomize
    can hijack).
    """
    path = "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
    env = {
        "HOME":   os.environ["HOME"],
        "USER":   os.environ.get("USER", ""),
        "TERM":   os.environ.get("TERM", "xterm-256color"),
        "SHELL":  os.environ.get("SHELL", "/bin/bash"),
        "LANG":   "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH":   path,
        # brew-built wget links against brew openssl which has its own default
        # CA path — invalid here. Point it at Apple's system CA bundle.
        "SSL_CERT_FILE":  "/etc/ssl/cert.pem",
        "CURL_CA_BUNDLE": "/etc/ssl/cert.pem",
    }
    if venv_bin:
        env["PATH"] = f"{venv_bin}:{path}"
        env["VIRTUAL_ENV"] = str(venv_bin.parent)
    if extras:
        env.update(extras)
    return env


def run(label: str, argv, env: dict, log_path: Path = None) -> int:
    hdr(label)
    info("$ " + " ".join(str(a) for a in argv))
    if log_path:
        with open(log_path, "wb") as f:
            r = subprocess.run(argv, env=env, stdout=f, stderr=subprocess.STDOUT)
        info(f"log: {log_path}  (rc={r.returncode})")
    else:
        r = subprocess.run(argv, env=env)
        info(f"rc={r.returncode}")
    return r.returncode


def is_macho(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) in MACHO_MAGICS
    except (OSError, IOError):
        return False


def scan_machos(root: Path) -> dict:
    """For every Mach-O in `root`, return {path: list of brew refs from otool -L}."""
    if not root.exists():
        return {}
    out = {}
    candidates = []
    for p in root.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        if p.suffix in (".dylib", ".so") or (p.suffix == "" and p.parent.name == "bin"):
            candidates.append(p)
    for p in candidates:
        if not is_macho(p):
            continue
        try:
            r = subprocess.run(["otool", "-L", str(p)],
                               capture_output=True, text=True, timeout=10)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
        refs = HOMEBREW_RE.findall(r.stdout)
        if refs:
            out[p] = refs
    return out


def _is_cmake_stdlib(p: Path) -> bool:
    """CMake's bundled Modules/ contain hardcoded /opt/homebrew strings as
    macOS search hints (FindGTK2, CMakeFindFrameworks, GNUInstallDirs, etc).
    These are upstream CMake source files, not OBT artifacts, and only
    affect downstream builds that *use* CMake's find_package — they're
    caught at that point by the artifact scan instead."""
    parts = p.parts
    if "cmake" in parts or any("cmake-" in pp for pp in parts):
        if "Modules" in parts or "Templates" in parts:
            return True
    return False


def _is_dep_source_tree(p: Path) -> bool:
    """A text file is upstream-dep-source if it lives under
    staging/builds/<dep>/ and NOT under that dep's .build/ subdir.
    Source-tree CI scripts, README snippets, etc. routinely contain
    /opt/homebrew references that aren't load-bearing for the OBT install.

    Also excludes FetchContent-pulled source under .../.build/_deps/<X>-src/,
    which is upstream code cmake downloaded mid-build (e.g. boost source
    pulled by igl's cmake)."""
    parts = p.parts
    try:
        idx = parts.index("builds")
    except ValueError:
        return False
    # parts[idx+1] = dep name, parts[idx+2] = first dir below it
    if idx + 2 >= len(parts):
        return False
    # Anything under .build/ is normally a build artifact — but cmake's
    # FetchContent_Declare extracts upstream source under .build/_deps/.
    if "_deps" in parts:
        di = parts.index("_deps")
        # parts[di+1] is e.g. "boost-src" — extracted upstream source.
        # Skip the entire subtree.
        if di + 1 < len(parts):
            return True
    return ".build" not in parts[idx+2:]


def scan_text(root: Path) -> dict:
    """Grep brew refs from text files (.cmake, .pc, pyvenv.cfg, etc.)."""
    if not root.exists():
        return {}
    out = {}
    for p in root.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        if _is_cmake_stdlib(p):
            continue
        if _is_dep_source_tree(p):
            continue
        try:
            txt = p.read_text(errors="ignore")
        except (OSError, IOError, UnicodeDecodeError):
            continue
        refs = HOMEBREW_RE.findall(txt)
        if refs:
            out[p] = refs
    return out


def filter_leaks(refs, allow_python: bool):
    """Return refs that are *not* allowed (i.e. real leaks)."""
    if allow_python:
        return [r for r in refs if not ALLOWED_RE.match(r)]
    return list(refs)


def report(label, machos, text, allow_python, root):
    hdr(label)
    by_pkg = {}
    leak_files = 0
    leak_total = 0

    for p, refs in sorted(machos.items()):
        leaks = filter_leaks(refs, allow_python)
        if not leaks:
            continue
        leak_files += 1
        leak_total += len(leaks)
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        print(f"  LEAK  {rel}")
        for r in sorted(set(leaks))[:8]:
            m = re.match(r"/opt/homebrew/(opt|Cellar)/([^/]+)/", r)
            pkg = m.group(2) if m else "?"
            by_pkg.setdefault(pkg, set()).add(rel)
            print(f"     -> {r}")

    for p, refs in sorted(text.items()):
        leaks = filter_leaks(refs, allow_python)
        if not leaks:
            continue
        leak_files += 1
        leak_total += len(leaks)
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        print(f"  LEAK  {rel}")
        for r in sorted(set(leaks))[:8]:
            m = re.match(r"/opt/homebrew/(opt|Cellar)/([^/]+)/", r)
            pkg = m.group(2) if m else "?"
            by_pkg.setdefault(pkg, set()).add(rel)
            print(f"     -> {r}")

    if not leak_files:
        print("  (clean)")
    elif by_pkg:
        print("\n  Summary by homebrew package:")
        for pkg in sorted(by_pkg):
            print(f"    {pkg:24s}  {len(by_pkg[pkg])} consumer(s)")
    return leak_files


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path,
        help="test root directory (will contain venv/ and staging/). Wiped unless --incremental.")
    ap.add_argument("--repo", type=Path, default=Path.home()/"projects"/"ork.build",
        help="ork.build source repo to pip-install from (default: ~/projects/ork.build)")
    ap.add_argument("--bootstrap-python", type=Path,
        default=Path("/opt/homebrew/bin/python3"),
        help="host python used to seed the venv — the ONLY allowed brew touch")
    ap.add_argument("--incremental", action="store_true",
        help="reuse existing venv/staging if present (still re-installs OBT)")
    ap.add_argument("--no-reinstall", action="store_true",
        help="skip pip install OBT (incremental mode only)")
    ap.add_argument("--scan-only", action="store_true",
        help="skip bootstrap; only run the leak scan")
    ap.add_argument("--skip-env-create", action="store_true",
        help="skip step 4 (obt.env.create.py). Useful to validate the venv/pip steps cheaply.")
    ap.add_argument("--build", default=None,
        help="comma-separated list of additional deps to build after env.create "
             "(e.g. --build jpegturbo,boost,luajit). Each one runs under the "
             "OBT env that env.create produced.")
    ap.add_argument("--project-dirs", default=None,
        help="colon-separated list of project directories to expose to deps "
             "via OBT_PROJECT_DIRS. Used by deps that detect a user working "
             "copy (e.g. orkid checks for orkid.cmake here before fetching "
             "from github).")
    args = ap.parse_args()

    root = args.root.resolve()
    repo = args.repo.resolve()
    venv = root/"venv"
    venv_bin = venv/"bin"
    staging = root/"staging"

    hdr("OBT no-homebrew bootstrap test")
    info(f"root            : {root}")
    info(f"repo            : {repo}")
    info(f"bootstrap-python: {args.bootstrap_python}")
    info(f"mode            : "
         + ("scan-only" if args.scan_only
            else ("incremental" if args.incremental else "fresh")))

    if not args.scan_only:
        if not args.bootstrap_python.exists():
            die(f"bootstrap python not found: {args.bootstrap_python}")
        if not (repo/"setup.py").exists():
            die(f"ork.build repo not found at: {repo}")

    # --- step 1: wipe ---
    if not args.scan_only and not args.incremental:
        hdr("Step 1: wipe")
        safe_wipe(root, repo)
        root.mkdir(parents=True)

    # --- step 2: create venv ---
    if not args.scan_only and not (args.incremental and venv.exists()):
        rc = run("Step 2: create venv (bootstrap python)",
                 [str(args.bootstrap_python), "-m", "venv", str(venv)],
                 sanitized_env())
        if rc != 0:
            die(f"venv creation failed (rc={rc})")

    # --- step 3: pip install ork.build from local repo ---
    if not args.scan_only and not args.no_reinstall:
        log = root/"pip_install.log"
        rc = run("Step 3: pip install ork.build (local repo, no PyPI)",
                 [str(venv_bin/"pip"), "install", "--upgrade", "--force-reinstall",
                  "--no-cache-dir", str(repo)],
                 sanitized_env(venv_bin), log_path=log)
        if rc != 0:
            die(f"pip install failed (rc={rc}); see {log}")

    # --- step 4: obt.env.create.py --stagedir ---
    env_create_rc = 0
    if not args.scan_only and not args.skip_env_create and not (args.incremental and staging.exists()):
        log = root/"env_create.log"
        env_create_rc = run("Step 4: obt.env.create.py --stagedir",
                 [str(venv_bin/"obt.env.create.py"), "--stagedir", str(staging)],
                 sanitized_env(venv_bin), log_path=log)
        if env_create_rc != 0:
            warn(f"env.create returned rc={env_create_rc} (bootstrap incomplete; running scan anyway)")

    # --- step 4b: build extra deps under the OBT env ---
    extra_build_rcs = {}
    if not args.scan_only and args.build and env_create_rc == 0:
        deps = [d.strip() for d in args.build.split(",") if d.strip()]
        # Use --stagedir (not --stack). --stack layers onto whatever OBT env
        # the parent shell already has, which leaks parent-staging vars into
        # the child build. --stagedir initializes a fresh OBT env from the
        # staging on disk, and the parent env is already sanitized() — so the
        # child sees a pristine OBT env rooted at this staging only.
        build_extras = {"OBT_STAGE": str(staging)}
        if args.project_dirs:
            build_extras["OBT_PROJECT_DIRS"] = args.project_dirs
        build_env = sanitized_env(venv_bin, extras=build_extras)
        for dep_name in deps:
            log = root/f"build_{dep_name}.log"
            cmd = f"obt.dep.build.py {dep_name}"
            rc = run(f"Step 4b: build dep '{dep_name}'",
                     [str(venv_bin/"obt.env.launch.py"),
                      "--stagedir", str(staging),
                      "--command", cmd],
                     build_env, log_path=log)
            extra_build_rcs[dep_name] = rc
            if rc != 0:
                warn(f"build of '{dep_name}' returned rc={rc} (continuing scan)")

    # --- step 5: scan ---
    hdr("Step 5: leak scan")
    info(f"scanning {venv} (bootstrap-python brew refs allowed)")
    venv_machos = scan_machos(venv)
    venv_text   = scan_text(venv)
    info(f"scanning {staging} (any /opt/homebrew ref is a leak)")
    stag_machos = scan_machos(staging)
    stag_text   = scan_text(staging)

    n_venv = report("venv leaks (excluding bootstrap python)",
                    venv_machos, venv_text, allow_python=True, root=root)
    n_stag = report("staging leaks (no /opt/homebrew allowed)",
                    stag_machos, stag_text, allow_python=False, root=root)

    print()
    failed_extra = [d for d, rc in extra_build_rcs.items() if rc != 0]
    if n_venv == 0 and n_stag == 0:
        if not args.scan_only and not args.skip_env_create and env_create_rc != 0:
            hdr(f"INCONCLUSIVE: leak scan clean but env.create failed (rc={env_create_rc}). "
                "Bootstrap did not complete; see env_create.log.")
            sys.exit(3)
        if failed_extra:
            hdr(f"INCONCLUSIVE: leak scan clean but extra dep build(s) failed: "
                + ", ".join(failed_extra))
            sys.exit(3)
        hdr("PASS: zero homebrew leakage (excluding bootstrap python in venv)")
        sys.exit(0)
    else:
        hdr(f"FAIL: {n_venv} venv leak(s), {n_stag} staging leak(s)")
        sys.exit(2)


if __name__ == "__main__":
    main()
