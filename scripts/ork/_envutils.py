import ork.env
import ork.host
import ork.path
import ork.dep
import ork.deco
import ork.command
import os, sys, re

deco = ork.deco.Deco()

##########################################

class EnvSetup:
  def __init__(self,stagedir=None,
                    rootdir=None,
                    projectdir=None,
                    bindir=None,
                    scriptsdir=None,
                    disable_syspypath=False,
                    is_quiet=False,
                    project_name=None,
                    git_ssh_command=None):

    if stagedir==None:
      stagedir = ork.path.Path(os.environ["OBT_STAGE"])
    if rootdir==None:
      rootdir = ork.path.Path(os.environ["OBT_ROOT"])
    if projectdir==None:
      projectdir = ork.path.Path(os.environ["OBT_PROJECT_DIR"])
    if bindir==None:
      bindir = rootdir/"bin"
    if scriptsdir==None:
      scriptsdir = rootdir/"scripts"
    if project_name==None and "OBT_PROJECT_NAME" in os.environ:
      project_name = os.environ["OBT_PROJECT_NAME"] 
    if git_ssh_command==None and "OBT_GIT_SSH_COMMAND" in os.environ:
      git_ssh_command = os.environ["OBT_GIT_SSH_COMMAND"] 

    self.OBT_STAGE = stagedir 
    self.ROOT_DIR = rootdir 
    self.PROJECT_DIR = projectdir 
    self.BIN_DIR = bindir 
    self.SCRIPTS_DIR = scriptsdir 
    self.DISABLE_SYSPYPATH=disable_syspypath
    self.IS_QUIET = is_quiet
    self.PROJECT_NAME = project_name
    self.GIT_SSH_COMMAND = git_ssh_command

  ##########################################
  def install(self):
    orig_path = ""
    orig_ld_library_path = ""
    orig_ps1 = ""
    orig_pkg_config = ""
    orig_pkg_config_path = ""
    orig_python_path = ""
    if "PATH" in os.environ:
      orig_path = os.environ["PATH"]
    if "PS1" in os.environ:
      orig_ps1 = os.environ["PS1"]
    if "LD_LIBRARY_PATH" in os.environ:
      orig_ld_library_path = os.environ["LD_LIBRARY_PATH"]
    if "PKG_CONFIG" in os.environ:
      orig_pkg_config = os.environ["PKG_CONFIG"]
    if "PKG_CONFIG_PATH" in os.environ:
      orig_pkg_config_path = os.environ["PKG_CONFIG_PATH"]
    if "PYTHONPATH" in os.environ:
      orig_python_path = os.environ["PYTHONPATH"]

    ork.env.set("color_prompt","yes")
    ork.env.set("OBT_STAGE",self.OBT_STAGE)
    ork.env.set("OBT_BUILDS",self.OBT_STAGE/"builds")
    ork.env.set("OBT_ROOT",self.ROOT_DIR)
    ork.env.set("OBT_PROJECT_DIR",self.PROJECT_DIR)
    ork.env.set("OBT_SUBSPACE","host")
    ork.env.set("OBT_SUBSPACE_PROMPT","host")
    ork.env.set("OBT_SUBSPACE_DIR",self.OBT_STAGE)
    ork.env.set("OBT_PROJECT_NAME",self.PROJECT_NAME)
    ork.env.set("OBT_ORIGINAL_PATH",orig_path )
    ork.env.set("OBT_ORIGINAL_LD_LIBRARY_PATH",orig_ld_library_path )
    ork.env.set("OBT_ORIGINAL_PS1",orig_ps1 )
    ork.env.set("OBT_ORIGINAL_PKG_CONFIG",orig_pkg_config )
    ork.env.set("OBT_ORIGINAL_PKG_CONFIG_PATH",orig_pkg_config_path )
    ork.env.set("OBT_ORIGINAL_PYTHONPATH",orig_python_path )
    ork.env.set("OBT_SCRIPTS_DIR",self.SCRIPTS_DIR )
    ork.env.set("OBT_PYTHONHOME",self.OBT_STAGE/"pyvenv")
    ork.env.set("OBT_SUBSPACE_LIB_DIR",ork.path.libs())
    ork.env.set("OBT_SUBSPACE_BIN_DIR",ork.path.bin())
    ork.env.prepend("PATH",self.BIN_DIR )
    ork.env.prepend("PATH",self.OBT_STAGE/"bin")
    ork.env.prepend("LD_LIBRARY_PATH",self.OBT_STAGE/"lib")
    ork.env.prepend("LD_LIBRARY_PATH",self.OBT_STAGE/"lib64")

    ork.env.append("OBT_MODULES_PATH",ork.path.root()/"modules")
    ork.env.append("OBT_DEP_PATH",ork.path.root()/"modules"/"dep")
    ork.env.set("OBT_GIT_SSH_COMMAND",self.GIT_SSH_COMMAND)

    obt_prj_extensions = self.PROJECT_DIR/"obt.project"
    if obt_prj_extensions.exists():
      self.importProject(obt_prj_extensions)

    if ork.host.IsLinux:

      if ork.host.IsDebian:
        pkgcfgdir = ork.path.Path("/lib/x86_64-linux-gnu/pkgconfig")
      elif ork.host.IsGentoo:
        pkgcfgdir = ork.path.Path("/usr/lib64/pkgconfig")
      elif ork.host.IsAARCH64:
        pkgcfgdir = ork.path.Path("/usr/lib/pkgconfig")

      if pkgcfgdir.exists():
        ork.env.append("PKG_CONFIG_PATH",pkgcfgdir)
      pkgcfgdir = ork.path.Path("/usr/share/pkgconfig")
      if pkgcfgdir.exists():
        ork.env.append("PKG_CONFIG_PATH",pkgcfgdir)
    elif ork.host.IsDarwin:
      pkgcfgdir = ork.path.Path("/usr/local/lib/pkgconfig")
      if pkgcfgdir.exists():
        ork.env.append("PKG_CONFIG_PATH",pkgcfgdir)


    if ork.path.vivado_base().exists():
        ork.env.append("PATH",ork.path.vivado_base()/"bin")
    
    #####################################
    # Python Env Init
    #####################################
    
    if not ork.host.IsAARCH64:
      PYTHON = ork.dep.instance("python")
    
    #####################################
    # Late init
    #####################################
    ork.env.set("PYTHONNOUSERSITE","TRUE")
    ork.env.append("PYTHONPATH",self.SCRIPTS_DIR)
    ork.env.prepend("PKG_CONFIG",self.OBT_STAGE/"bin"/"pkg-config")
    #ork.env.prepend("PKG_CONFIG_PREFIX",self.OBT_STAGE)
    ork.env.prepend("PKG_CONFIG_PATH",self.OBT_STAGE/"lib"/"pkgconfig")
    ork.env.prepend("PKG_CONFIG_PATH",self.OBT_STAGE/"lib64"/"pkgconfig")
    ork.env.append("PYTHONPATH",self.OBT_STAGE/"lib"/"python")
    ork.env.append("LD_LIBRARY_PATH",self.OBT_STAGE/"python-3.9.13"/"lib")

    
  ###########################################

  def importProject(self,prjdir):
    init_script = prjdir/"scripts"/"init_env.py"
    #print(init_script)
    if init_script.exists():
      import importlib
      modulename = importlib.machinery.SourceFileLoader('modulename',str(init_script)).load_module()
      #print(modulename)
      modulename.setup()
      #modul.setup()
    modules_dir = prjdir/"modules"
    #print(modules_dir,modules_dir.exists())
    if modules_dir.exists():
      ork.env.prepend("OBT_MODULES_PATH",modules_dir)

  ###########################################
  def log(self,x):
    if not self.IS_QUIET:
       print(x)
  ###########################################
  def lazyMakeDirs(self):
    self.log(deco.bright("Making required directories"))
    (ork.path.prefix()/"lib").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"bin").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"include").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"sdks").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"tempdir").mkdir(parents=True,exist_ok=True)
    (ork.path.subspace_root()).mkdir(parents=True,exist_ok=True)
    (ork.path.quarantine()).mkdir(parents=True,exist_ok=True)
    ork.path.downloads().mkdir(parents=True,exist_ok=True)
    ork.path.builds().mkdir(parents=True,exist_ok=True)
    ork.path.manifests().mkdir(parents=True,exist_ok=True)
    ork.path.gitcache().mkdir(parents=True,exist_ok=True)
    ork.path.apps().mkdir(parents=True,exist_ok=True)
    ork.path.buildlogs().mkdir(parents=True,exist_ok=True)
  ###########################################
  def genLaunchScript(self,out_path=None,subspace=None):
    numcores = int(os.environ["OBT_NUM_CORES"])

    LAUNCHENV = []
    if self.GIT_SSH_COMMAND!=None:
      LAUNCHENV += ['export GIT_SSH_COMMAND="%s";'%self.GIT_SSH_COMMAND]
    LAUNCHENV += ["%s/bin/init_env.py" % self.ROOT_DIR]
    LAUNCHENV += ["--numcores", numcores]
    LAUNCHENV += ["--launch", self.OBT_STAGE]
    LAUNCHENV += ["--prjdir", self.PROJECT_DIR]

    if subspace!= None:
      LAUNCHENV += ["--subspace", subspace]

    LAUNCHENV += [";\n"]

    f = open(str(out_path), 'w')
    f.write(" ".join(ork.command.procargs(LAUNCHENV)))
    f.close()
    os.system("chmod ugo+x %s"%str(out_path))

  ###########################################
  def genBashRc(self,out_path=None,override_sysprompt=None):
    self.log(deco.bright("Generating bashrc override_sysprompt<%s>"%override_sysprompt))
    bdeco = ork.deco.Deco(bash=True)

    BASHRC = ""

    ################################################
    # generate prompt
    ################################################

    stackindic = ""
    stacked = False
    if "OBT_STACK" in os.environ:
      stackindic = os.environ["OBT_STACK"]
      stacked = True

    ####################
    # system prompt (leftmost icon in prompt)

    SYSPROM = ""
    if ork.host.IsOsx:    
      SYSPROM = "🍎"
    elif ork.host.IsLinux:    
      SYSPROM = "🐧"

    if "OBT_USE_PROMPT_PREFIX" in os.environ:
      SYSPROM = os.environ["OBT_USE_PROMPT_PREFIX"]

    if override_sysprompt!=None:
      SYSPROM = override_sysprompt

    PROMPT = bdeco.promptL('%s[ %s %s-${OBT_SUBSPACE_PROMPT} ]'%(SYSPROM,stackindic,self.PROJECT_NAME))
    PROMPT += bdeco.promptC("\\w")
    PROMPT += bdeco.promptR("[$(parse_git_branch) ]")
    PROMPT += bdeco.bright("> ")

    ################################################
    # The sanity of this is a little debatable.
    #  on the one hand, some of the user's shell customizations are respected
    #  on the other hand this can perturb the build environment in other unexpected ways..
    ################################################

    if (os.path.exists("~/.bashrc")):
      BASHRC += 'source $HOME/.bashrc;\n' # source users's bash setup

    ################################################

    BASHRC += 'parse_git_branch() { git branch 2> /dev/null | grep "*" | sed -e "s/*//";};\n'

    BASHRC += 'export -f parse_git_branch\n'

    BASHRC += "\nexport PS1='%s';\n" % PROMPT
    BASHRC += "alias ls='ls -G';\n"
    BASHRC += "complete -r -v\n"

    #########################################
    # statically defined goto and push methods
    #########################################

    dirs = {
        "root": "${OBT_ROOT}",
        "project": "${OBT_PROJECT_DIR}",
        "deps": "${OBT_ROOT}/modules/dep",
        "subspace": "${OBT_STAGE}/subspaces/${OBT_SUBSPACE}",
        "stage": "${OBT_STAGE}",
        "builds": "${OBT_STAGE}/builds",
        "litex": "${OBT_STAGE}/builds/litex_env", # todo convert obt.litex.env.py to litex dep
    }

    #########################################
    # dynamic goto and pushd methods
    #  generated from individual deps
    #########################################

    depitems = ork.dep.DepNode.FindWithMethod("env_goto")
    for depitemk in depitems:
      depitem = depitems[depitemk]
      gotos = depitem.env_goto()
      dirs.update(gotos)

    #########################################

    for k in dirs:
        v = dirs[k]
        BASHRC += "obt.goto.%s() { cd %s; };" % (k,v)
        BASHRC += "obt.push.%s() { pushd %s; };" % (k,v)

    if out_path!=None:
      f = open(str(out_path), 'w')
      f.write(BASHRC)
      f.close()

    return BASHRC
