#!/usr/bin/env python3
import time
from obt import path, command, docker
time.sleep(2)
##############################################
ssltest_dir = docker.dir_of_module("ssltest")
ssltest = docker.descriptor("ssltest")
##############################################
while(not ssltest._manifest_path.exists()):
  print("waiting for manifest<%s>..." % ssltest._manifest_path)
  time.sleep(3)
##############################################
time.sleep(3)
cmd_to_run = ssltest_dir/"examples"/"test-zmq-ping-multi.py"
command.run([cmd_to_run], do_log=True)
# wait for ctrl-c
print("\n\nPress Ctrl-C to stop the test...")
try:
  while True:
    time.sleep(1)
except KeyboardInterrupt:
  exit(0)
