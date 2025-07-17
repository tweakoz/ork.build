#!/usr/bin/env python3

from obt import path, command, docker

module = docker.descriptor("ssltest")
module.build([])
module.launch([])

 
