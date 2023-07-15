#!/usr/bin/env python3
from obt import macos, path
binpath = path.bin()/"obt.tool.release"
macos.macho_replace_loadpaths(binpath, "@rpath/", "@yopath/")
macos.macho_dump(binpath)