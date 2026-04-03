#!/usr/bin/env python3
################################################################
# Install OBT Claude Code skills to ~/.claude/skills/
#
# Copies skill files from the OBT installation to the user's
# ~/.claude/skills/ directory so Claude Code can discover them
# in any project.
#
# Usage:
#   obt.claude.setup.py          # install skills
#   obt.claude.setup.py --check  # check if installed
#   obt.claude.setup.py --remove # remove installed skills
################################################################

import os
import sys
import shutil
import argparse
from pathlib import Path

def get_obt_skills_source():
    """Find installed OBT claude skills directory."""
    venv_data = os.environ.get("OBT_VENV_DATA")
    if venv_data:
        src = Path(venv_data) / "claude_skills"
        if src.exists():
            return src
    # Fallback: look relative to this script
    script_dir = Path(__file__).resolve().parent
    for candidate in [
        script_dir.parent / "claude_skills",
        script_dir.parent / "obt" / "claude_skills",
    ]:
        if candidate.exists():
            return candidate
    return None

def get_user_skills_dir():
    """Get ~/.claude/skills/ path."""
    return Path.home() / ".claude" / "skills"

def install_skills(source_dir, dest_dir, verbose=True):
    """Copy skill directories from source to dest."""
    installed = []
    for skill_dir in sorted(source_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_name = skill_dir.name
        dest_skill = dest_dir / skill_name
        dest_skill.mkdir(parents=True, exist_ok=True)
        for f in skill_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, dest_skill / f.name)
        installed.append(skill_name)
        if verbose:
            print(f"  Installed: {skill_name} -> {dest_skill}")
    return installed

def check_skills(source_dir, dest_dir):
    """Check if skills are installed and up to date."""
    all_ok = True
    for skill_dir in sorted(source_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_name = skill_dir.name
        dest_skill = dest_dir / skill_name / "SKILL.md"
        src_skill = skill_dir / "SKILL.md"
        if not dest_skill.exists():
            print(f"  {skill_name}: NOT INSTALLED")
            all_ok = False
        elif src_skill.exists():
            src_mtime = src_skill.stat().st_mtime
            dst_mtime = dest_skill.stat().st_mtime
            if src_mtime > dst_mtime:
                print(f"  {skill_name}: OUT OF DATE")
                all_ok = False
            else:
                print(f"  {skill_name}: OK")
        else:
            print(f"  {skill_name}: OK (no source to compare)")
    return all_ok

def remove_skills(source_dir, dest_dir, verbose=True):
    """Remove OBT-installed skills from user directory."""
    removed = []
    for skill_dir in sorted(source_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_name = skill_dir.name
        dest_skill = dest_dir / skill_name
        if dest_skill.exists():
            shutil.rmtree(dest_skill)
            removed.append(skill_name)
            if verbose:
                print(f"  Removed: {skill_name}")
    return removed

def main():
    parser = argparse.ArgumentParser(
        description="Install OBT Claude Code skills to ~/.claude/skills/")
    parser.add_argument("--check", action="store_true",
                        help="Check if skills are installed")
    parser.add_argument("--remove", action="store_true",
                        help="Remove installed skills")
    args = parser.parse_args()

    source = get_obt_skills_source()
    if not source:
        print("ERROR: Cannot find OBT claude_skills directory")
        print("  Checked $OBT_VENV_DATA/claude_skills/ and script-relative paths")
        sys.exit(1)

    dest = get_user_skills_dir()
    print(f"Source: {source}")
    print(f"Dest:   {dest}")

    if args.check:
        ok = check_skills(source, dest)
        sys.exit(0 if ok else 1)
    elif args.remove:
        removed = remove_skills(source, dest)
        print(f"Removed {len(removed)} skill(s)")
    else:
        installed = install_skills(source, dest)
        print(f"Installed {len(installed)} skill(s)")

if __name__ == "__main__":
    main()
