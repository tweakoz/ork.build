# ORK.BUILD TOOLS (OBT)  

### BuildStatus

* Ubuntu 19.10 [![CISTATUS](http://tweakoz.com:16999/orkdotbuild-ix-ub1910/master/status.svg)](http://tweakoz.com:16999/)
* Ubuntu 20.04 [![CISTATUS](http://tweakoz.com:16999/orkdotbuild-ix-ub2004/master/status.svg)](http://tweakoz.com:16999/)
* Osx Catalina [![CISTATUS](http://tweakoz.com:16999/orkdotbuild-osx-catalina/master/status.svg)](http://tweakoz.com:16999/)

### DESCRIPTION  

**ork.build** is a posix (Linux,OSX) *container based* build environment which provides shared functionality for common build automation tasks. **ork.build** also has a set of dependency providers for useful libraries. Unlike homebrew and apt the dependency provider interface is consistent regardless if you are on OSX or Linux - in general the entire interface is consistent on both OSX and Linux. ork.build is implemented primarily in python3. If you need to compose a set of build products with a unified set of versions and configuration data, then ork.build might be for you. It is also important to realize that ork.build is not a replacement for docker style containers. ork.build is specifically a build container environment, as opposed to a machine or microservice container environment. For example, one might use ork.build to prep content for use in a docker container. 

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
obt.dep.require.py boost
```

**to get list of obt commands:** (from bash shell)

we use bash's command line completion and ork.build's convention of prefixing all public commands with *obt*

```
obt.<tab tab>
```

**which returns:** (example)

```
obt.dep.list.py obt.dep.require.py obt.find.py
```



**to get list of obt dependency providers:**

```
obt.dep.list.py
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

