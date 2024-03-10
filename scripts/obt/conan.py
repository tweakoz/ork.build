from obt import command, path, pathtools, sdk, dep, subspace

prefix = path.subspace_dir()

the_environ = {
  "CONAN_HOME": prefix/"conan",
  "CONAN_USER_HOME": prefix/"conan",
  "CONAN_CACHE_DIR": "~/.obt-global/conan2"
}

##############################################

def environment():
  return the_environ

##############################################
# generate conanfile
##############################################

# missing 
# glfw
# lexertl14
# parsertl14
# easyprof 
# rtmidi 
# cpppeglib 
# klein 
# portaudio 

# not working
#libigl/2.3.0
#openimageio/2.5.6
#rapidjson/cci.20230929 <incompatible with assimp/5.2.2>
#openblas/0.3.26 
#"libsndfile/1.2.2",

#lexertl = dep.instance("lexertl14")
#print(lexertl)
#print(dir(lexertl))

conanfile = """
[requires]
zlib/1.2.11
boost/1.81.0
assimp/5.2.2
ptex/2.4.2
openexr/3.2.1
rapidjson/cci.20220822
eigen/3.4.0
glm/cci.20230113
bullet3/3.25
zeromq/4.3.5
cppzmq/4.10.0
sigslot/1.2.2 
moltenvk/1.2.2
lexertl14/tweakoz-obt
"zeromq/4.3.4",
"zmqpp/4.2.0",
"tracy/cci.20220130",
"stb/cci.20230920"
  "sqlite3/3.45.0",
  "sqlitecpp/3.3.1",
  "libbacktrace/cci.20210118",
  "audiofile/1.1.1",
  "alembic/1.8.6",
[generators]
CMakeDeps
CMakeToolchain
"""
  
def require(prefix,build_dir,deplist):

  conanfile = "[requires]\n"

  for item in deplist:
    conanfile += f"{item}\n"

  conanfile += "\n"
  conanfile += "[generators]\n"
  conanfile += "CMakeDeps\n"
  conanfile += "CMakeToolchain\n"

  cf_output = build_dir/"conanfile.txt"
  with open(cf_output,"w") as f:
    f.write(conanfile)

  ##############################################
    
  cmd =  ["conan","install","."]
  cmd += [f"--profile:host={prefix}/ios.host.profile"]
  cmd += [f"--profile:build={prefix}/ios.build.profile"]
  cmd += ["--build=missing"]

  command.run(cmd, #
              environment=the_environ, #
              working_dir=build_dir, #
              do_log=True)
