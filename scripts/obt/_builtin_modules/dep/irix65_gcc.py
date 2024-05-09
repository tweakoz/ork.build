###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile, sys
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import _gcc

deco = Deco()

###############################################################################

class irix65_gcc(dep.Provider):

    def __init__(self): ############################################
        super().__init__("irix65_gcc")
        self._archlist = ["x86_64"]


    ########

    def __str__(self):
        return "irix65 GCC (source)"

    ########

    def wipe(self):
        os.system("rm -rf %s"%self.source_root)
        os.system("rm -rf %s"%self.build_dest)

    ########

    def provide(self): ##########################################################
        if True: #False==self.OK:

            toolchain_dir = path.prefix()/"opt"/"toolchain"/"mips-sgi-irix6.5"
            self.toolchain_dir = toolchain_dir
            ###############################################
            ## fetch and extract irix 6.5.30 development sysroot
            ###############################################
            self.irixroot_fname = "irix-root.6.5.30.tar.bz2"
            self.irixroot_extract_dir = toolchain_dir/"irix6.5.30-sysroot"
            if self.irixroot_extract_dir.exists():
                os.system("chmod -R ugo+w %s"%self.irixroot_extract_dir)
                os.system("rm -rf %s"%self.irixroot_extract_dir)
            self.irixroot_arc = dep.downloadAndExtract(["http://mirror.larbob.org/compilertron/irix-root.6.5.30.tar.bz2"],
                                                        self.irixroot_fname,
                                                        "bz2",
                                                        "bb9a2d81729b23327207e6af30fd241f",
                                                        self.irixroot_extract_dir)
            ###############################################
            # patch gcc
            ###############################################
            gccpatchdir = path.patches()/"gcc"
            gcc_patches = [gccpatchdir/"gcc.sgifixes.patch",
                           gccpatchdir/"gcc.sgifixlibstdcpp01.patch",
                           gccpatchdir/"gcc.sgifixlibstdcpp02.patch"]
            newlib_patches = [gccpatchdir/"newlib.sgifixes.patch"]
            ###############################################
            # build it
            ###############################################
            binutils = dep.require("irix65_binutils")
            gcc = _gcc.context("mips-sgi-irix65",gccpatches=gcc_patches,newlibpatches=newlib_patches)
            bdest = gcc.build_dir/".build"
            pfx = path.prefix()
            os.mkdir(bdest)
            os.chdir(bdest)
            return gcc.build( target="mips-sgi-irix6.5",
                              variant="newlib",
                              program_prefix="mips-sgi-irix6.5-",
                              install_prefix=self.toolchain_dir,
                              with_ld=toolchain_dir/"bin"/"mips-sgi-irix6.5-ld",
                              with_as=toolchain_dir/"bin"/"mips-sgi-irix6.5-as",
                              with_build_sysroot=self.irixroot_extract_dir,
                              with_dwarf2=True
                              )

            """cmd = Command(['../configure',
                           '--prefix=%s'%toolchain_dir,
                           '--target=mips-sgi-irix6.5',
                           '--enable-languages=c,c++',
                           '--disable-nls',
                           '--disable-libssp',
                           #'--with-dwarf2'
                           #'--with-ld=%s'%(toolchain_dir/"bin"/"mips-sgi-irix6.5-ld"),
                           #'--with-as=%s'%(toolchain_dir/"bin"/"mips-sgi-irix6.5-as"),
                           #'--with-build-sysroot=%s'%self.irixroot_extract_dir,
                           '--disable-shared',
                           '--disable-threads',
                           '--disable-libgomp',
                           '--libdir=%s'%(toolchain_dir/"lib"/"mips-sgi-irix6.5-gcc"/gcc.version),
                           ])"""

            #cmd.exec()
            #make.exec()
            #make.exec("install",parallelism=0.0)

            #self.OK = True
            #self.manifest.touch()
            #return self.OK

"""
../libgcc/../gcc -I../../../../libgcc/../include  -DHAVE_CC_TLS  -o _gcov_dump.o -MT _gcov_dump.o -MD -MP -MF _gcov_dump.dep -DL_gcov_dump -c ../../../../libgcc/libgcov-interface.c
In file included from ../../../../libgcc/unwind-dw2.c:412:
./md-unwind-support.h:37:10: fatal error: signal.h: No such file or directory
37 | #include <signal.h>
|          ^~~~~~~~~~
compilation terminated.
"""

"""

projects/staging-obt/builds/gcc-mips-sgi-irix65/gcc-10.1.0/.build-stage2/./gcc/xgcc -B/projects/staging-obt/builds/gcc-mips-sgi-irix65/gcc-10.1.0/.build-stage2/./gcc/ -B//mips-sgi-irix6.5/bin/ -B//mips-sgi-irix6.5/lib/ -isystem //mips-sgi-irix6.5/include -isystem //mips-sgi-irix6.5/sys-include --sysroot=/projects/staging-obt/opt/toolchain/mips-sgi-irix6.5/irix6.5.30-sysroot   -g -O2 -mabi=64 -O2 -g -O2 -DIN_GCC  -DCROSS_DIRECTORY_STRUCTURE  -W -Wall -Wno-narrowing -Wwrite-strings -Wcast-qual -Wstrict-prototypes -Wmissing-prototypes -Wold-style-definition  -isystem ./include  -I. -I. -I../../.././gcc -I../../../../libgcc -I../../../../libgcc/. -I../../../../libgcc/../gcc -I../../../../libgcc/../include   -g0  -finhibit-size-directive -fno-inline -fno-exceptions -fno-zero-initialized-in-bss -fno-toplevel-reorder -fno-tree-vectorize -fbuilding-libgcc -fno-stack-protector  -Dinhibit_libc  -I. -I. -I../../.././gcc -I../../../../libgcc -I../../../../libgcc/. -I../../../../libgcc/../gcc -I../../../../libgcc/../include  -o irix-crtn.o -MT irix-crtn.o -MD -MP -MF irix-crtn.dep -c ../../../../libgcc/config/mips/irix-crtn.S


In file included from ../../../../libgcc/unwind-dw2.c:412:
./md-unwind-support.h:37:10: fatal error: signal.h: No such file or directory
37 | #include <signal.h>
"""