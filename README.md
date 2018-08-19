# ORK.BUILD TOOLS (OBT)

### STATUS

[TravisCI(OSX)](https://travis-ci.org/tweakoz/ork.build) ![Build Status](https://travis-ci.org/tweakoz/ork.build.svg?branch=master)


[CirrusCI(IX)](https://api.cirrus-ci.com/github/tweakoz/ork.build) ![Build Status](https://api.cirrus-ci.com/github/tweakoz/ork.build.svg)



### DESCRIPTION

**ork.build** is a posix (Linux,OSX) *container based* build environment which provides shared functionality for common build automation tasks. **ork.build** also has a set of dependency providers for useful libraries, unlike homebrew or apt the dependency provider interface is consistent regardless if you are on OSX or Linux - in general the entire interface is consitent on both OSX and Linux. ork.build is implemented primarily in python3. 


### USAGE

**to create (and launch) an environment:**

```
git clone https://github.com/tweakoz/ork.build 
ork.build/bin/init_env.py --create <staging_folder>
```


**to relaunch an environment container:**
*(the container remembers and references the original ork.build folder)*

```
<staging_folder>/.launch_env
```

**to install a dependency:** (into the container)

eg. boost
```
obt_dep_require.py boost
```

**to get list of obt commands:** (from bash shell)

we use bash's command line completion and ork.build's convention of prefixing all public commands with *obt*

```
obt_<tab tab>
```

**which returns:** (example)

```
obt_dep_list.py obt_dep_require.py obt_find.py
```



**to get list of obt dependency providers:**

```
obt_dep_list.py
```

**which returns:** (example)


```
ork.build dependency provider list:

assimp binutils_avr binutils_lm32 boost gcc_avr gcc_lm32
gcode_gpr gitpython glfw irrlicht luajit minetest oiio
postgresql qt5 simavr unittestpp wt4 yarl
```
 



### HISTORY

**ork.build** historically derives from [orkid's build system](https://github.com/tweakoz/orkid/tree/master/ork.build), [micro_ork's build system](https://github.com/tweakoz/micro_ork/tree/master/ork.build) in conjunction with concepts from orkid's ['tozkit'](https://github.com/tweakoz/orkid/tree/master/tozkit) dependency provider system, [homebrew](https://brew.sh/), [apt](https://wiki.debian.org/Apt), and other build systems and package managers I have worked with over the years.

