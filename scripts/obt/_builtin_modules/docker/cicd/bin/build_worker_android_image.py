#!/usr/bin/env python3 

import os, ci_common 

os.environ["DOCKER_BUILDKIT"]="1"

cmdlist = list()

cmdlist += ["docker","build"]
cmdlist += ["-f", "worker-android.dockerfile"]
cmdlist += ["-t", "obtcicd/worker_android"]
cmdlist += ["."]

ci_common.sync_subprocess(cmdlist)

