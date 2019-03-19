import ork, os
from ork.command import Command

VER = "8.1.0"
HASH = "65f7c65818dc540b3437605026d329fc"

NEWLIB_VER = "3.1.0"
NEWLIB_HASH = "f84263b7d524df92a9c9fb30b79e0134"

class context:
    def __init__(self,tgt):
        self.target = tgt
        self.version = VER
        self.name = "gcc-%s" % VER
        self.xzname = "%s.tar.xz" % self.name
        self.archive_file = ork.path.downloads()/self.xzname
        self.url = "https://ftp.gnu.org/gnu/gcc/gcc-%s/%s"%(VER,self.xzname)
        self.extract_dir = ork.path.builds()/("gcc-%s"%tgt)
        self.build_dir = self.extract_dir/self.name

        self.arcpath = ork.dep.downloadAndExtract([self.url],
                                                   self.xzname,
                                                   "xz",
                                                   HASH,
                                                   self.extract_dir)


        self.newlib_xzname = "newlib-%s.tar.gz" % NEWLIB_VER
        self.newlib_extract_dir = ork.path.builds()/("newlib-%s" % NEWLIB_VER)

        self.newlib_arc = ork.dep.downloadAndExtract(["ftp://sourceware.org/pub/newlib/%s"%self.newlib_xzname],
                                                      self.newlib_xzname,
                                                      "gz",
                                                      NEWLIB_HASH,
                                                      self.newlib_extract_dir)


    #############################################

    def build(self,
              variant="newlib",
              languages="c,c++",
              enable_set=set(),
              disable_set=set(),
              prefix=ork.path.prefix(),
              program_prefix=None
              ):

        assert(self.target!=None)

        ######################################

        if program_prefix==None:
            program_prefix = self.target+"-"

        ######################################

        def set2opts(pfx,the_set):
            opts = list()
            for item in list(the_set):
                opts += ["%s%s"%(pfx,item)]
            return opts

        ######################################
        # required options
        ######################################

        base_build_opts = [ '--prefix=%s'%prefix,
                            '--target=%s'%self.target ]

        ######################################
        # variant - newlib, default(stdc++, etc)
        ######################################


        if variant=="newlib":

            do_gcc = True
            do_newlib = True

            if do_gcc:
                os.chdir(self.build_dir)
                ork.command.run(["rm","-rf","libstdc++-v3"])

            build_dest = self.build_dir/".build-with_newlib"

            enable_set = enable_set | set(["threads=single","multilib"])
            disable_set = disable_set | set(["shared","libssp","libatomic",
                                             "libgomp","libmudflap","libquadmath",
                                             "nls","tls","libgcc"])

            # STAGE 1

            stg1_opts = ['--with-headers=%s'%str(self.newlib_extract_dir/"newlib"/"libc"/"include")]
            stg1_opts += ['--with-newlib']

            stg1_opts += set2opts("--disable-",disable_set)
            stg1_opts += set2opts("--enable-",enable_set)

            stg1_opts += ['--program-prefix=%s'%program_prefix]
            stg1_opts += ['--enable-languages=c,c++']
            stg1_opts += ['--prefix=/']

            if do_gcc:
                os.environ["NEWLIB"] = str(self.newlib_extract_dir)
                os.chdir(self.extract_dir)
                os.system( "ln -s ../${NEWLIB}/newlib .")
                os.system( "ln -s ../${NEWLIB}/libgloss .")
                self._build( base_build_opts + stg1_opts, build_dest, prefix )

            #######################
            # build newlib
            #######################

            if do_newlib:
              nlbd = self.newlib_extract_dir/".build"
              os.system("rm -rf %s"%nlbd)
              os.mkdir(nlbd)
              os.chdir(nlbd)
              ork.command.run([ "../newlib-%s/configure"%NEWLIB_VER,
                                "--target=%s"%self.target,
                                "--prefix=/",
                                "--disable-newlib-supplied-syscalls",
                                "--enable-multilib"])
              ork.command.run(["make"])
              ork.command.system(["make","DESTDIR=%s"%prefix,"install"])

        else: # // default, stdc++
            assert(False)
            pass

        ######################################


    #############################################

    def _build(self,build_opts,bdest,prefix):
        os.mkdir(bdest)
        os.chdir(bdest)
        ork.command.run(['../configure']+build_opts)
        ork.make.exec("all")
        ork.command.system(["make","DESTDIR=%s"%prefix,"install"])
