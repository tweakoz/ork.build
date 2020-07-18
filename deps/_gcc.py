import ork, os
from ork.command import Command

VER = "10.1.0"
HASH = "7d48e00245330c48b670ec9a2c518291"

NEWLIB_VER = "3.3.0"
NEWLIB_HASH = "af1c64d25eb3f71dec5ad7ec79877d7f"

class context:
    def __init__(self,provider):
        self.version = VER
        self.name = "gcc-%s" % VER
        self.xzname = "%s.tar.xz" % self.name
        self.archive_file = ork.path.downloads()/self.xzname
        self.url = "https://ftp.gnu.org/gnu/gcc/gcc-%s/%s"%(VER,self.xzname)
        self.extract_dir = ork.path.builds()/("gcc-%s"%provider._name)
        self.build_dir = self.extract_dir/self.name
        self.arcpath = ork.dep.downloadAndExtract([self.url],
                                                   self.xzname,
                                                   "xz",
                                                   HASH,
                                                   self.extract_dir)


        self.newlib_xzname = "newlib-%s.tar.gz" % NEWLIB_VER
        self.newlib_extract_dir = ork.path.builds()/("newlib-%s" % provider._name)

        self.newlib_arc = ork.dep.downloadAndExtract(["ftp://sourceware.org/pub/newlib/%s"%self.newlib_xzname],
                                                      self.newlib_xzname,
                                                      "gz",
                                                      NEWLIB_HASH,
                                                      self.newlib_extract_dir)


    #############################################

    def build(self,
              target=None,
              variant="newlib",
              languages="c,c++",
              enable_set=set(),
              disable_set=set(),
              install_prefix=ork.path.prefix(),
              program_prefix=None
              ):

        assert(target!=None)
        self.target = target
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

        base_build_opts = [ '--prefix=%s'%install_prefix,
                            '--target=%s'%self.target ]
        base_build_opts += ['--enable-languages=c,c++']
        base_build_opts += ['--prefix=/']

        ######################################
        # variant - newlib, default(stdc++, etc)
        ######################################


        if variant=="newlib":

            do_gcc = True
            do_newlib = True

            #######################

            if do_gcc:
                os.chdir(self.build_dir)
                ork.command.run(["rm","-rf","libstdc++-v3"])

            enable_set = enable_set | set(["threads=single","multilib"])
            disable_set = disable_set | set(["shared","libssp","libatomic",
                                             "libgomp","libmudflap","libquadmath",
                                             "nls","tls", "libstdcxx"])

            #######################

            base_build_opts += ['--with-newlib'] # dont build with or against glibc
            base_build_opts += set2opts("--disable-",disable_set)
            base_build_opts += set2opts("--enable-",enable_set)

            #######################
            # STAGE 1
            #######################

            if do_gcc:
                stg1_opts = ['--with-headers=%s'%str(self.newlib_extract_dir/"newlib"/"libc"/"include")] # no system headres
                stg1_opts += ['--program-prefix=%s-'%target]
                stg1_opts += ["--disable-libgcc"]
                os.environ["NEWLIB"] = str(self.newlib_extract_dir)
                os.chdir(self.extract_dir)
                os.system( "ln -s ${NEWLIB}/newlib .")
                os.system( "ln -s ${NEWLIB}/libgloss .")
                build_dest = self.build_dir/".build-stage1"
                if not self._build( base_build_opts + stg1_opts, build_dest, install_prefix ):
                  return False

            #######################
            # build newlib
            #######################

            if do_newlib:
              env = os.environ
              env["PATH"] = env["PATH"]+":"+str(install_prefix/"bin")
              nlbd = self.newlib_extract_dir/".build"
              os.system("rm -rf %s"%nlbd)
              os.mkdir(nlbd)
              os.chdir(nlbd)
              if ork.command.run([ "../newlib-%s/configure"%NEWLIB_VER,
                                  "--target=%s"%target,
                                  "--prefix=/",
                                  "--disable-newlib-supplied-syscalls",
                                  "--enable-multilib"],environment=env)!=0:
                return False
              if ork.command.run(["make"])!=0:
                return False
              if ork.command.system(["make","DESTDIR=%s"%install_prefix,"install"])!=0:
                return False

            #######################
            # STAGE 2
            #######################

            #--with-local-prefix=/tools # gcc search path prefix
            #--with-native-system-header-dir=/tools/include # gcc headers search path


            if do_gcc:
                stg2_opts = ['--program-prefix=%s'%program_prefix]
                stg2_opts += ["--enable-libgcc"]
                os.environ["NEWLIB"] = str(self.newlib_extract_dir)
                os.chdir(self.extract_dir)
                build_dest = self.build_dir/".build-stage2"
                if not self._build( base_build_opts + stg2_opts, build_dest, install_prefix ):
                   return False

        else: # // default, stdc++
            assert(False)
            pass

        return True

        ######################################


    #############################################

    def _build(self,build_opts,bdest,install_prefix):
        os.mkdir(bdest)
        os.chdir(bdest)
        if ork.command.run(['../configure']+build_opts)!=0:
          return False
        if ork.make.exec("all")!=0:
          return False
        if ork.command.system(["make","DESTDIR=%s"%install_prefix,"install"])!=0:
          return False
        return True
