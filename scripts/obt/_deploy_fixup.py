###############################################################################
# obt._deploy_fixup
#
# Launch-time fixup for relocated deployments.
#
# A deployment built by ork.deploy.macos.relocatable.py contains text files
# with absolute paths baked to the original target directory. If the deploy
# is moved to a new location, those paths break.
#
# This module detects relocation and patches text files so the deployment
# works from any directory. It is designed to be called from any launcher
# script (shell launcher, GUI app, etc.) before the main OBT environment
# is initialized.
#
# Usage from a launcher:
#   from obt._deploy_fixup import fixup_if_relocated
#   fixup_if_relocated("/path/to/deploy")
#
# The fixup is idempotent and fast on subsequent launches (skipped when the
# marker file matches the current location).
###############################################################################

import os
import sys

# Marker file written at the deploy root to record the "known good" path.
_MARKER_FILENAME = ".deploy_path"

###############################################################################
# Public API
###############################################################################

def fixup_if_relocated(deploy_root):
  """Check if the deployment has been moved and fix paths if so.

  This is the main entry point. Call it from any launcher before
  initializing the OBT environment.

  Args:
    deploy_root: Absolute path to the deployment root directory.

  Returns:
    True if a fixup was performed, False if no fixup was needed.
  """
  deploy_root = os.path.realpath(deploy_root)
  marker_path = os.path.join(deploy_root, _MARKER_FILENAME)

  old_root = _read_marker(marker_path)
  if old_root == deploy_root:
    return False  # No relocation — fast path

  if old_root is None:
    # First run or marker missing — write marker, no fixup needed
    # (paths should already match from the build)
    _write_marker(marker_path, deploy_root)
    return False

  # Deployment was moved: old_root → deploy_root
  print(f"[deploy-fixup] Relocation detected:")
  print(f"  old: {old_root}")
  print(f"  new: {deploy_root}")

  count = _apply_fixup(deploy_root, old_root)

  print(f"[deploy-fixup] Fixed {count} files.")
  _write_marker(marker_path, deploy_root)
  return True

###############################################################################
# Fixup implementation
###############################################################################

# Directories (relative to deploy root) containing text files that need fixup.
# Each entry is (rel_dir, file_filter) where file_filter is a callable.
_FIXUP_TARGETS = [
  # Venv configs — critical for Python to find its stdlib
  ("obt_venv", lambda f: f == "pyvenv.cfg"),
  ("pyvenv",   lambda f: f == "pyvenv.cfg"),

  # Venv bin scripts (pip, activate, etc.)
  ("obt_venv/bin", lambda f: not f.endswith(('.pyc',))),
  ("pyvenv/bin",   lambda f: not f.endswith(('.pyc',))),

  # pkg-config files
  ("lib/pkgconfig",   lambda f: f.endswith('.pc')),
  ("lib64/pkgconfig", lambda f: f.endswith('.pc')),

  # CMake config files
  ("lib/cmake", lambda f: f.endswith('.cmake')),
]

def _apply_fixup(deploy_root, old_root):
  """Replace old_root with deploy_root in all known text files.

  Args:
    deploy_root: New absolute path to the deployment.
    old_root: Previous absolute path embedded in text files.

  Returns:
    Number of files modified.
  """
  count = 0

  for rel_dir, file_filter in _FIXUP_TARGETS:
    abs_dir = os.path.join(deploy_root, rel_dir)
    if not os.path.isdir(abs_dir):
      continue
    for fname in os.listdir(abs_dir):
      if not file_filter(fname):
        continue
      fpath = os.path.join(abs_dir, fname)
      if not os.path.isfile(fpath) or os.path.islink(fpath):
        continue
      if _fix_file(fpath, old_root, deploy_root):
        count += 1

  return count


def _fix_file(fpath, old_str, new_str):
  """Replace old_str with new_str in a single text file.

  Returns True if the file was modified.
  """
  try:
    with open(fpath, 'r', errors='replace') as f:
      content = f.read()
  except (OSError, UnicodeDecodeError):
    return False

  if old_str not in content:
    return False

  content = content.replace(old_str, new_str)
  try:
    with open(fpath, 'w') as f:
      f.write(content)
  except OSError:
    return False

  return True

###############################################################################
# Marker file
###############################################################################

def _read_marker(marker_path):
  """Read the deploy path marker. Returns None if absent or unreadable."""
  try:
    with open(marker_path, 'r') as f:
      return f.read().strip()
  except (OSError, ValueError):
    return None


def _write_marker(marker_path, deploy_root):
  """Write the deploy path marker."""
  try:
    with open(marker_path, 'w') as f:
      f.write(deploy_root + '\n')
  except OSError:
    pass  # Non-fatal — fixup will just re-run next time
