#!/usr/bin/env python3
from ork import osx, path
binpath = path.bin()/"ork.tool.release"
osx.macho_replace_loadpaths(binpath, "@rpath/", "@yopath/")
osx.macho_dump(binpath)