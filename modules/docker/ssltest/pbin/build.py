#!/usr/bin/env python3 

import os, proctools, argparse, sys
from obt import path, deco
deco = deco.Deco()

os.environ["DOCKER_BUILDKIT"] = "1"

parser = argparse.ArgumentParser(description='ZMQ SSL Example Docker Builder (OBT compatible)')
parser.add_argument('--service', choices=['zmq-server', 'ssl-proxy', 'all'], 
                   default='all', help='Which service to build')

args, unknown_args = parser.parse_known_args()

cmdlist = ["docker", "compose", "build"]

# Add service-specific build if requested
if args.service != 'all':
    cmdlist.append(args.service)

# Add any additional build args from OBT
cmdlist.extend(unknown_args)

proctools.sync_subprocess(cmdlist)

