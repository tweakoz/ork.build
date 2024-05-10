#!/usr/bin/env python3

from obt import  path, command, wget, pathtools, host
from yarl import URL

assert(host.IsLinux and host.IsX86_64)

plugin_dir = path.home()/".docker"/"cli-plugins"
dl_url = URL("https://github.com")/"docker"/"buildx"/"releases"/"download"/"v0.11.2"/"buildx-v0.11.2.linux-amd64"
out_file = plugin_dir/"docker-buildx"

pathtools.ensureDirectoryExists(plugin_dir)
command.run(["curl","-sSL",dl_url,"-o", out_file],do_log=True)
command.run(["chmod","+x", out_file],do_log=True)

