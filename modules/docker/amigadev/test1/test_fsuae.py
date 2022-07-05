#!/usr/bin/env python3 

from yarl import URL
from ork import command, path, pathtools, wget


builddir = path.builds()/"amigadev-test1"
pathtools.chdir(builddir)

archive = URL("https://archive.org/download")

# fetch kickstarts
zipname = "Amiga-Kickstart-ROMs-Commodore-A500-A600-A1000-A3000-A4000-A1200-A2000.zip"
url = archive/"amiga-kickstart-roms-commodore-a-500-a-600-a-1000-a-3000-a-4000-a-1200-a-2000"/zipname
wget.wget( urls=[url],
           output_name=path.downloads()/zipname,
           md5val="2765730b20470e7001d656d1f49b721d")
command.run(["unzip","-o",path.downloads()/zipname])

# fetch DOS disk
zipname = "AmigaDOS CLI rev 27.5 (1985)(Commodore)[m].zip"
wget.wget( urls=[archive/"CommodoreAmigaApplicationsADF"/zipname],
           output_name=path.downloads()/zipname,
           md5val="f5b9e49849dc04ddb35b1d6de3155fa2")
command.run(["unzip","-o",path.downloads()/zipname])

command.run(["fs-uae",
             "--hard_drive_0=.",
             "--floppy-drive-0=%s"%str(builddir/"img.adf"),
             "--amiga-model=a4000 ",
             "--kickstart_file=./Kickstart-v3.1-rev40.70-1994-Commodore-A4000.rom",
             "--floppy_drive_volume=0"])
