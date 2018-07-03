###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect
from pathlib import Path

def deps():
  root = Path(os.environ["ORKDOTBUILD_ROOT"])
  return root/"deps"

def prefix():
  staging = Path(os.environ["ORK_STAGING_FOLDER"])
  return staging

def manifests():
  staging = Path(os.environ["ORK_STAGING_FOLDER"])
  return staging/"manifests"

def downloads():
  staging = Path(os.environ["ORK_STAGING_FOLDER"])
  return staging/"downloads"

def gitcache():
  staging = Path(os.environ["ORK_STAGING_FOLDER"])
  return staging/"gitcache"

def builds():
  staging = Path(os.environ["ORK_STAGING_FOLDER"])
  return staging/"builds"
