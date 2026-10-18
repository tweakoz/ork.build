#!/usr/bin/env python3
"""Clone and relocate an OBT staging tree for an independent build lane.

The destination is created through a sibling temporary directory and published
with one rename only after relocation and verification succeed.  On macOS the
default copy uses APFS clonefile semantics; a full copy requires explicit opt-in.
Linux ELF relocation requires readelf and patchelf. Compiled-in resource paths
and other references that cannot be safely relocated cause validation to fail.
"""

import argparse
import datetime
import json
import mmap
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile

# A checkout invocation must use its matching helpers, even inside an older
# installed OBT environment. Installed bin scripts use their normal package.
checkout_scripts = Path(__file__).resolve().parents[1] / "scripts"
if (checkout_scripts / "obt" / "stage_binary.py").is_file():
    sys.path.insert(0, str(checkout_scripts))
from obt import macos
from obt.stage_binary import runtime_prefix_references


RUNTIME_ROOTS = ("bin", "lib", "pyvenv", "cmake", "include", "manifests", "share")
def command(argv, *, capture=False, check=True):
    return subprocess.run(
        [str(x) for x in argv], check=check, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None)


def canonical(text):
    return Path(text).expanduser().resolve()


def reject_unsafe(source, dest):
    home = Path.home().resolve()
    if not source.is_dir():
        raise SystemExit(f"source stage is not a directory: {source}")
    if dest.exists() or dest.is_symlink():
        raise SystemExit(f"destination already exists: {dest}")
    if source == dest or source in dest.parents or dest in source.parents:
        raise SystemExit("source and destination must be distinct, non-nested paths")
    if source in (Path("/"), home) or dest in (Path("/"), home):
        raise SystemExit("refusing filesystem root or home directory as a stage")
    if not (source / "obt-launch-env").is_file() or not (source / "lib").is_dir():
        raise SystemExit("source does not look like an OBT staging tree")
    dest.parent.mkdir(parents=True, exist_ok=True)


def clone_tree(source, temp, full_copy):
    if sys.platform == "darwin" and not full_copy:
        if os.stat(source).st_dev != os.stat(dest_parent := temp.parent).st_dev:
            raise SystemExit(f"APFS clone requires the same filesystem: {source} and {dest_parent}")
        command(["cp", "-cRp", f"{source}/.", temp])
        return "macos-clonefile"
    if not full_copy:
        raise SystemExit("copy-on-write cloning is unavailable; pass --full-copy explicitly")
    shutil.copytree(source, temp, symlinks=True, copy_function=shutil.copy2)
    return "full-copy"


def iter_files(root):
    for base, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for name in dirs:
            candidate = Path(base) / name
            if candidate.is_symlink():
                yield candidate
        for name in names:
            yield Path(base) / name


def rewrite_text(root, old, new):
    old_bytes, new_bytes = str(old).encode(), str(new).encode()
    changed = []
    for path in iter_files(root):
        if path.is_symlink():
            continue
        try:
            if path.stat().st_size > 16 * 1024 * 1024:
                continue
            data = path.read_bytes()
        except (OSError, PermissionError):
            continue
        if b"\0" in data[:4096] or old_bytes not in data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.write_bytes(data.replace(old_bytes, new_bytes))
        path.chmod(mode)
        changed.append(str(path.relative_to(root)))
    return changed


def rewrite_symlinks(root, old, new):
    changed = []
    for base, dirs, names in os.walk(root):
        for name in dirs + names:
            path = Path(base) / name
            if not path.is_symlink():
                continue
            target = os.readlink(path)
            if target == str(old) or target.startswith(str(old) + os.sep):
                relocated = str(new) + target[len(str(old)):]
            elif not os.path.isabs(target):
                relative = path.relative_to(root)
                original_target = (Path(old) / relative.parent / target).resolve()
                if not original_target.is_relative_to(old):
                    continue
                relocated = os.path.relpath(Path(new) / original_target.relative_to(old),
                                            Path(new) / relative.parent)
                if relocated == target:
                    continue
            else:
                continue
            path.unlink()
            path.symlink_to(relocated)
            changed.append(str(path.relative_to(root)))
    return changed


def relocate_macho(root, old, new):
    changed = macos.macho_relocate_prefix(root, old, new, skip_dirs=set())
    for record in changed:
        record["path"] = str(Path(record["path"]).relative_to(root))
    return changed


def is_elf(path):
    with path.open("rb") as stream:
        return stream.read(4) == b"\x7fELF"


def elf_paths(path):
    """Inspect active loader metadata; failures must not certify a broken clone."""
    env = dict(os.environ, LC_ALL="C")
    result = subprocess.run(["readelf", "--wide", "--dynamic", "--program-headers", str(path)],
                            check=True, capture_output=True, text=True, env=env)
    values = []
    for line in result.stdout.splitlines():
        match = re.search(r"\((NEEDED|SONAME|RPATH|RUNPATH)\).*\[(.*)\]", line)
        if match:
            values.append(match.groups())
        match = re.search(r"\[Requesting program interpreter: (.*)\]", line)
        if match:
            values.append(("INTERP", match.group(1)))
    return values


def relocate_elf(root, old, new):
    """Preserve ELF layout and RPATH semantics while relocating absolute paths."""
    old, new = str(old), str(new)
    def replace(value):
        return new + value[len(old):] if value == old or value.startswith(old + "/") else value
    changed = []
    for path in iter_files(root):
        if path.is_symlink() or not is_elf(path):
            continue
        edits = []
        for kind, value in elf_paths(path):
            replacement = ":".join(map(replace, value.split(":"))) if kind in ("RPATH", "RUNPATH") else replace(value)
            if replacement == value:
                continue
            options = {"NEEDED": ["--replace-needed", value, replacement],
                       "SONAME": ["--set-soname", replacement],
                       "INTERP": ["--set-interpreter", replacement],
                       "RPATH": ["--force-rpath", "--set-rpath", replacement],
                       "RUNPATH": ["--set-rpath", replacement]}[kind]
            command(["patchelf", *options, path], capture=True)
            edits.append((kind, value, replacement))
        if edits:
            changed.append({"path": str(path.relative_to(root)), "edits": edits})
    return changed


def purge_bytecode(root):
    removed = 0
    for base, dirs, names in os.walk(root, topdown=False):
        for name in names:
            if name.endswith(".pyc"):
                (Path(base) / name).unlink()
                removed += 1
        for name in dirs:
            if name == "__pycache__":
                shutil.rmtree(Path(base) / name)
    return removed


def run_existing_fixup(stage, projects):
    launcher = shutil.which("obt.env.launch.py")
    if not launcher:
        raise SystemExit("OBT launcher is not available in the active virtualenv")
    argv = [launcher, "--quiet", "--stagedir", stage]
    for project in projects:
        argv += ["--project", project]
    argv += ["--command", "obt.osx.macho.fixup.libs.py --alllibs --orkpymods"]
    command(argv)


def finalize_macho_signatures(root):
    """Verify the final bytes, repairing signatures invalidated by fixup."""
    resigned = []
    for path in macos.discover_macho_files(root, skip_dirs=set()):
        if command(["codesign", "--verify", path], capture=True, check=False).returncode:
            command(["codesign", "--force", "--sign", "-", path], capture=True)
            command(["codesign", "--verify", path], capture=True)
            resigned.append(str(Path(path).relative_to(root)))
    return resigned


def old_prefix_findings(root, old):
    needle = str(old).encode()
    findings = {"text": [], "symlink": [], "macho": [], "elf": [], "binary_embedded": []}
    for name in RUNTIME_ROOTS + ("obt-launch-env", ".bashrc"):
        subtree = root / name
        paths = [subtree] if subtree.is_file() or subtree.is_symlink() else list(iter_files(subtree)) if subtree.is_dir() else []
        for path in paths:
            if path.is_symlink():
                if str(old) in os.readlink(path) or path.resolve().is_relative_to(old):
                    findings["symlink"].append(str(path.relative_to(root)))
                continue
            if sys.platform.startswith("linux") and is_elf(path):
                for kind, value in elf_paths(path):
                    if str(old) in value:
                        findings["elf"].append({"path": str(path.relative_to(root)), "kind": kind, "value": value})
            runtime_reference = runtime_prefix_references(path, old)
            if runtime_reference is not None:
                if runtime_reference:
                    findings["binary_embedded"].append(str(path.relative_to(root)))
                continue
            # No size cutoff and no ignored read failures: an incomplete scan
            # cannot establish independence. mmap keeps large files off the heap.
            with path.open("rb") as stream:
                if os.fstat(stream.fileno()).st_size == 0:
                    continue
                with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
                    if data.find(needle) < 0:
                        continue
                    kind = "binary_embedded" if b"\0" in data[:4096] else "text"
                    findings[kind].append(str(path.relative_to(root)))
    if sys.platform == "darwin":
        findings["macho"] = [
            {**item, "path": str(Path(item["path"]).relative_to(root))}
            for item in macos.macho_find_prefix_references(root, old, skip_dirs=set())]
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--full-copy", action="store_true")
    parser.add_argument("--skip-macho-fixup", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    source, dest = canonical(args.source), canonical(args.dest)
    reject_unsafe(source, dest)
    temp = Path(tempfile.mkdtemp(prefix=f".{dest.name}.clone-", dir=dest.parent))
    temp.rmdir()  # cp/copytree require a nonexistent destination
    try:
        method = clone_tree(source, temp, args.full_copy)
        text_changed = rewrite_text(temp, source, dest)
        symlinks_changed = rewrite_symlinks(temp, source, dest)
        bytecode_removed = purge_bytecode(temp)
        macho_changed = relocate_macho(temp, source, dest) if sys.platform == "darwin" else []
        elf_changed = relocate_elf(temp, source, dest) if sys.platform.startswith("linux") else []
        # The existing fixer is a required normalization layer, but cannot run
        # until the tree has its final path because OBT resolves the stage.
        (temp / ".obt-stage-clone-incomplete").write_text("validation in progress\n")
        temp.rename(dest)
        if sys.platform == "darwin" and not args.skip_macho_fixup:
            run_existing_fixup(dest, [str(canonical(x)) for x in args.project])
        # Verify after the final normalization pass, which may edit binaries
        # that were already verified and signed during prefix relocation.
        findings = old_prefix_findings(dest, source)
        if any(findings.values()):
            raise RuntimeError(f"source-stage references remain: {findings}")
        resigned = finalize_macho_signatures(dest) if sys.platform == "darwin" else []
        (dest / ".obt-stage-clone-incomplete").unlink()
        manifest = {
            "schema": "obt.stage.clone.v1",
            "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "host": platform.platform(), "source": str(source), "destination": str(dest),
            "copy_method": method, "projects": [str(canonical(x)) for x in args.project],
            "text_files_rewritten": text_changed, "symlinks_rewritten": symlinks_changed,
            "macho_files_rewritten": macho_changed, "macho_files_resigned": resigned,
            "elf_files_rewritten": elf_changed,
            "bytecode_files_removed": bytecode_removed,
            "verification": {"source_prefix_findings": findings, "passed": True},
        }
        (dest / "obt-stage-clone.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(dest)
    except BaseException:
        if dest.exists() and not temp.exists():
            dest.rename(temp)
        if temp.exists():
            shutil.rmtree(temp)
        raise


if __name__ == "__main__":
    main()
