###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# Published under the GPL 2.0 license
###############################################################################
"""ArmorPaint (3D PBR texture painter) from the user's mirror tweakoz/armorpaint.

Pinned to main @ c5ccdf2 (2026-09-18), fetched as a GitHub tarball of the full sha.

Upstream needs no Node/Haxe/submodules: base/make runs a committed prebuilt
QuickJS tool (base/tools/bin/<platform>/amake) on base/tools/make.js, which
generates native project files and drives the platform toolchain. On macOS that
is an Xcode project built with xcodebuild (Metal backend); on Linux a Makefile
built with make + clang (Vulkan backend). The app uses only system libraries, so
it is installed self-contained under <stage>/apps with a launcher in <stage>/bin.
"""
import os
import shutil
from obt import dep, host, path
from obt.command import Command

REVISION = "c5ccdf27818a36e67decb691009a3db457d59ab3"
APP = "ArmorPaint"


def _graphics():
  return "metal" if host.IsOsx else "vulkan"


def make_command():
  return ["../base/make", "--graphics", _graphics(), "--compile"]


def app_dir():
  return path.stage()/"apps"/(APP + ".app" if host.IsOsx else "armorpaint")


def app_executable():
  if host.IsOsx:
    return app_dir()/"Contents"/"MacOS"/APP
  return app_dir()/APP


def launcher():
  return path.stage()/"bin"/"armorpaint"


class armorpaint(dep.StdProvider):
  name = "armorpaint"

  def __init__(self):
    super().__init__(armorpaint.name)
    self._oslist = ["Darwin", "Linux"]
    self._archlist = ["x86_64", "aarch64"]

  @property
  def supports_host(self):
    # the macOS amake/Metal path is only exercised on Apple silicon
    return super().supports_host and not (host.IsOsx and not host.IsAARCH64)

  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=armorpaint.name, repospec="tweakoz/armorpaint",
                             revision=REVISION, recursive=False)

  def build_output(self):
    # macOS: xcodebuild runs with cwd=paint/build, so its default SYMROOT adds
    # another build/; Linux: make.js copies the exe into its data dir build/out
    if host.IsOsx:
      return self.source_root/"paint"/"build"/"build"/"Release"/(APP + ".app")
    return self.source_root/"paint"/"build"/"out"

  def build(self):
    if not self.areRequiredSourceFilesPresent():
      return False
    tools = self.source_root/"base"/"tools"
    for exe in (self.source_root/"base"/"make", tools/"bin"/("macos" if host.IsOsx else
                ("linux_arm64" if host.IsAARCH64 else "linux_x64"))/"amake"):
      os.chmod(exe, 0o755)
    return Command(make_command(), working_dir=self.source_root/"paint").exec() == 0

  def install(self):
    src = self.build_output()
    if not (src/(("Contents/MacOS/" + APP) if host.IsOsx else APP)).exists():
      print("armorpaint: build output missing: %s" % src)
      return False
    dst = app_dir()
    if dst.exists():
      shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, symlinks=True)
    launcher().parent.mkdir(parents=True, exist_ok=True)
    launcher().write_text('#!/bin/sh\nexec "%s" "$@"\n' % app_executable())
    os.chmod(launcher(), 0o755)
    return True

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"base"/"make").exists() and \
           (self.source_root/"paint"/"project.js").exists()

  def areRequiredBinaryFilesPresent(self):
    return launcher().exists() and app_executable().exists()

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()
