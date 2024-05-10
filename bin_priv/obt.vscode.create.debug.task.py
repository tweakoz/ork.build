#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import argparse, sys, os, json
from ork import env, path

parser = argparse.ArgumentParser(description='ork.build environment launcher')
parser.add_argument("-w", '--working-dir', metavar="workdir", help='launch from pre-existing folder' )
parser.add_argument("-p", '--project-dir', metavar="prjdir", help='override project directory' )
parser.add_argument("-c", '--command', metavar="command", help="execute in environ")
parser.add_argument("-x", '--subspace', metavar="subspace", default ="host", help='subspace to launch' )
parser.add_argument("-o", '--output', metavar="output", help='output json file' )

args = vars(parser.parse_args())

# get env vars from os.environ

PATH = os.environ["PATH"]
ORKID_WORKSPACE_DIR = os.environ["ORKID_WORKSPACE_DIR"]
OBT_STAGE = os.environ["OBT_STAGE"]
OBT_STAGE = os.environ["OBT_STAGE"]
OBT_ROOT = os.environ["OBT_ROOT"]
OBT_SUBSPACE = os.environ["OBT_SUBSPACE"]
LD_LIBRARY_PATH = os.environ["LD_LIBRARY_PATH"]

# create vs code launch json data structure for debug, including env vars

launch_json = {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "ork.build",
            "type": "cppdbg",
            "request": "launch",
            "program": "${workspaceFolder}/ork.build/bin/obt",
            "args": [
                "--launch",
                "${workspaceFolder}",
                "--subspace",
                "host",
                "--command",
                "bash"
            ],
            "stopAtEntry": False,
            "cwd": "${workspaceFolder}",
            "environment": []

        }
    ]
}

# add env vars to launch json

for item in [
    "PATH",
    "ORKID_WORKSPACE_DIR",
    "OBT_STAGE",
    "OBT_STAGE",
    "OBT_ROOT",
    "OBT_SUBSPACE",
    "LD_LIBRARY_PATH"
]:
    launch_json["configurations"][0]["environment"].append({
        "name": item,
        "value": os.environ[item]
    })  

# write launch json to file

if args["output"]!=None:
    with open(args["output"], 'w') as outfile:
        json.dump(launch_json, outfile, indent=4)

