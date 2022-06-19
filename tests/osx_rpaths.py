#!/usr/bin/env python3
from ork import macos, path
binpath = path.bin()/"ork.tool.release"
macos.macho_replace_loadpaths(binpath, "@rpath/", "@yopath/")
macos.macho_dump(binpath)