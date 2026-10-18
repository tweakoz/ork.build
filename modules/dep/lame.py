###############################################################################
# Orkid Build System — pinned LAME encoder for FFmpeg/DAW audio export.
# LAME 3.100: LGPL-2.0-or-later. Source archive SHA256:
# ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e
###############################################################################
from yarl import URL
from obt import dep, path

VERSION = "3.100"
BASENAME = "lame-" + VERSION
FILENAME = BASENAME + ".tar.gz"
MD5 = "83e260acbe4389b54fe08e0bdbf7cddb"

class lame(dep.StdProvider):
    name = "lame"

    def __init__(self):
        super().__init__(self.name)
        self.setSourceRoot(path.builds()/self.name/BASENAME)
        self._builder = self.createBuilder(dep.AutoConfBuilder)
        for option in ("--disable-static", "--enable-shared", "--disable-dependency-tracking",
                       "--disable-debug", "--disable-nasm"):
            self._builder.setOption(option)

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(self.name)
        f._url = URL("https://downloads.sourceforge.net/project/lame/lame/3.100/")/FILENAME
        f._fname = FILENAME
        f._arctype = "tgz"
        f._md5 = MD5
        return f

    def build(self):
        # Upstream3.100 exports lame_init_old although it is not implemented.
        # Modern Darwin linkers reject it. Apply the same narrow correction
        # as the upstream LAME mailing-list/Homebrew recipe, including cached
        # source directories, without introducing a package-manager dependency.
        symbols = self.source_root/"include"/"libmp3lame.sym"
        original = symbols.read_text()
        corrected = original.replace("lame_init_old\n", "")
        if corrected != original:
            symbols.write_text(corrected)
        return super().build()

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"configure").is_file()

    def areRequiredBinaryFilesPresent(self):
        return ((path.libs()/("libmp3lame."+self.shlib_extension)).is_file()
                and (path.includes()/"lame"/"lame.h").is_file()
                and (path.bin()/"lame").is_file())

    @property
    def should_build(self):
        return super().should_build or not self.areRequiredBinaryFilesPresent()

    def onPostInstall(self):
        import json, shutil
        target = path.prefix()/"share"/"lame"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.source_root/"COPYING", target/"COPYING")
        (target/"source.json").write_text(json.dumps(dict(
            name="LAME", version=VERSION, license="LGPL-2.0-or-later",
            source_url="https://downloads.sourceforge.net/project/lame/lame/3.100/"+FILENAME,
            source_sha256="ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e",
            patch="Remove obsolete unimplemented lame_init_old export"), indent=2)+"\n")
        return True

    @property
    def root(self):
        return path.prefix()
