#!/usr/bin/env python3

import os, argparse, sys, pathlib

from _obt_config import configFromEnvironment
config = configFromEnvironment()

config.dump()