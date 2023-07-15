#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import obt.host, obt.sdk

from obt import dep, path
from obt.deco import Deco
deco = Deco()


h = obt.host.description()
host_sdk = obt.sdk.descriptor(h.architecture,h.os)

host_id = "%s.%s" % (h.architecture,h.os)

def print_item(key,val):
 dstr = deco.inf(host_id)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

print_item("architecture",h.architecture)
print_item("os",h.os)
print_item("revision",h.revision)
print_item("codename",h.codename)

targets = list()

for item in h.targets:
	tname = item.identifier
	targets += [tname]

print_item("targets",targets)

print_item("hostsdk.c_compiler",host_sdk.c_compiler)
print_item("hostsdk.cxx_compiler",host_sdk.cxx_compiler)

