import obt.env
import obt.host
import obt.path
import obt.deco
import obt.command
import os, sys, re, json

deco = obt.deco.Deco()


def validate_prompt(ps1_string):

  # check for balanced \[ and \]
  open_count = ps1_string.count('\\[')
  close_count = ps1_string.count('\\]')
  if open_count != close_count:
    print(f"Mismatch detected: {open_count} '\\[' found and {close_count} '\\]' found.")
    assert(False)

  # check that all ANSI escape sequences are inside \[\] pairs
  ansi_outside = re.findall(r"(?<!\\\[)(\033\[[^m]*m)(?!\\\])", ps1_string)
  if ansi_outside:
    print(f"Found ANSI escape sequences outside of '\\[' and '\\]': {ansi_outside}")
    assert(False)

##########################################

def root_path():
  import obt.path
  if obt.path.running_from_pip():
    return obt.path.obt_data_base()
  elif "OBT_ROOT" in os.environ:
    return obt.path.Path(os.environ["OBT_ROOT"])
  else:
    return None

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
      stagedir = obt.path.Path(os.environ["OBT_STAGE"])
    if rootdir==None:
      rootdir = root_path()
    if bindir==None:
      bindir = rootdir/"bin"
    if projectdir==None:
      projectdir = obt.path.Path(os.environ["OBT_PROJECT_DIR"])
    try_project_manifest = projectdir/"obt.project"/"obt.manifest"
    if try_project_manifest.exists():
      try_project_bin = projectdir/"obt.project"/"bin"
      if try_project_bin.exists():
        obt.env.append("PATH",try_project_bin)

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
    import obt.path
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

    ##############################################################################
    # retrieve original PKG_CONFIG_PATH
    ##############################################################################

    orig_pkg_config_path = obt.command.capture(["pkg-config","--variable","pc_path","pkg-config"])
    orig_pkg_config_path = orig_pkg_config_path.replace("\n","")
    print("orig_pkg_config_path<%s>"%orig_pkg_config_path)

    if "PKG_CONFIG" in os.environ:
      orig_pkg_config = os.environ["PKG_CONFIG"]
    #if "PKG_CONFIG_PATH" in os.environ:
    #  orig_pkg_config_path = os.environ["PKG_CONFIG_PATH"]
    if "PYTHONPATH" in os.environ:
      orig_python_path = os.environ["PYTHONPATH"]

    obt.env.set("PKG_CONFIG_PATH",orig_pkg_config_path )
    obt.env.set("OBT_ORIGINAL_PKG_CONFIG_PATH",orig_pkg_config_path )

    obt.env.set("OBT_ORIGINAL_PKG_CONFIG",orig_pkg_config )

    ##############################################################################

    obt.env.set("color_prompt","yes")
    obt.env.set("OBT_STAGE",self.OBT_STAGE)
    obt.env.set("OBT_BUILDS",self.OBT_STAGE/"builds")
    obt.env.set("OBT_ROOT",self.ROOT_DIR)
    obt.env.set("OBT_PROJECT_DIR",self.PROJECT_DIR)
    obt.env.set("OBT_SUBSPACE","host")
    obt.env.set("OBT_SUBSPACE_PROMPT","host")
    obt.env.set("OBT_SUBSPACE_DIR",self.OBT_STAGE)
    obt.env.set("OBT_PROJECT_NAME",self.PROJECT_NAME)
    obt.env.set("OBT_ORIGINAL_PATH",orig_path )
    obt.env.set("OBT_ORIGINAL_LD_LIBRARY_PATH",orig_ld_library_path )
    obt.env.set("OBT_ORIGINAL_PS1",orig_ps1 )
    obt.env.set("OBT_ORIGINAL_PYTHONPATH",orig_python_path )
    obt.env.set("OBT_SCRIPTS_DIR",self.SCRIPTS_DIR )
    obt.env.set("OBT_PYTHONHOME",self.OBT_STAGE/"pyvenv")
    obt.env.set("OBT_SUBSPACE_LIB_DIR",obt.path.libs())
    obt.env.set("OBT_SUBSPACE_BIN_DIR",obt.path.bin())
    obt.env.prepend("PATH",self.BIN_DIR )
    obt.env.prepend("PATH",self.OBT_STAGE/"bin")
    obt.env.prepend("LD_LIBRARY_PATH",self.OBT_STAGE/"lib")
    obt.env.prepend("LD_LIBRARY_PATH",self.OBT_STAGE/"lib64")

    obt.env.append("OBT_MODULES_PATH",obt.path.modules())
    obt.env.append("OBT_DEP_PATH",obt.path.modules()/"dep")

    if self.GIT_SSH_COMMAND!=None:
      obt.env.set("OBT_GIT_SSH_COMMAND",self.GIT_SSH_COMMAND)

    obt_prj_extensions = self.PROJECT_DIR/"obt.project"
    print(self.PROJECT_DIR)
    if obt_prj_extensions.exists():
      self.importProject(obt_prj_extensions)


    #if obt.host.IsLinux:

      #if obt.host.IsDebian:
      #  pkgcfgdir = obt.path.Path("/lib/x86_64-linux-gnu/pkgconfig")
      #elif obt.host.IsGentoo:
      #  pkgcfgdir = obt.path.Path("/usr/lib64/pkgconfig")
      #elif obt.host.IsAARCH64:
      #  pkgcfgdir = obt.path.Path("/usr/lib/pkgconfig")

      #if pkgcfgdir.exists():
      #  obt.env.append("PKG_CONFIG_PATH",pkgcfgdir)
      #pkgcfgdir = obt.path.Path("/usr/share/pkgconfig")
      #if pkgcfgdir.exists():
      #  obt.env.append("PKG_CONFIG_PATH",pkgcfgdir)
    #elif obt.host.IsDarwin:
      #pkgcfgdir = obt.path.Path("/usr/local/lib/pkgconfig")
      #if pkgcfgdir.exists():
      #  obt.env.append("PKG_CONFIG_PATH",pkgcfgdir)


    if obt.path.vivado_base().exists():
        obt.env.append("PATH",obt.path.vivado_base()/"bin")
    
    #####################################
    # Python Env Init
    #####################################
    
    if not obt.host.IsAARCH64:
      PYTHON = obt.dep.instance("python")
    
    #####################################
    # Late init
    #####################################
    obt.env.prepend("PKG_CONFIG",self.OBT_STAGE/"bin"/"pkg-config")
    #obt.env.prepend("PKG_CONFIG_PREFIX",self.OBT_STAGE)
    obt.env.prepend("PKG_CONFIG_PATH",self.OBT_STAGE/"lib"/"pkgconfig")
    obt.env.prepend("PKG_CONFIG_PATH",self.OBT_STAGE/"lib64"/"pkgconfig")

    if True: # WIP
      obt.env.set("PYTHONNOUSERSITE","TRUE")
      obt.env.append("PYTHONPATH",self.SCRIPTS_DIR)
      obt.env.prepend("PYTHONPATH",self.OBT_STAGE/"lib"/"python")
      obt.env.append("LD_LIBRARY_PATH",self.OBT_STAGE/"python-3.9.13"/"lib")

    if obt.path.running_from_pip():
      obt.env.prepend("PATH",obt.path.obt_data_base()/"bin_priv")

    
  ###########################################

  def importProject(self,prjdir):
    init_script = prjdir/"scripts"/"obt.env.extension.py"
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
      obt.env.prepend("OBT_MODULES_PATH",modules_dir)

  ###########################################
  def log(self,x):
    if not self.IS_QUIET:
       print(x)
  ###########################################
  def lazyMakeDirs(self):
    self.log(deco.bright("Making required directories"))
    (obt.path.prefix()/"lib").mkdir(parents=True,exist_ok=True)
    (obt.path.prefix()/"bin").mkdir(parents=True,exist_ok=True)
    (obt.path.prefix()/"include").mkdir(parents=True,exist_ok=True)
    (obt.path.prefix()/"sdks").mkdir(parents=True,exist_ok=True)
    (obt.path.prefix()/"tempdir").mkdir(parents=True,exist_ok=True)
    (obt.path.subspace_root()).mkdir(parents=True,exist_ok=True)
    (obt.path.quarantine()).mkdir(parents=True,exist_ok=True)
    obt.path.downloads().mkdir(parents=True,exist_ok=True)
    obt.path.builds().mkdir(parents=True,exist_ok=True)
    obt.path.manifests().mkdir(parents=True,exist_ok=True)
    obt.path.gitcache().mkdir(parents=True,exist_ok=True)
    obt.path.apps().mkdir(parents=True,exist_ok=True)
    obt.path.buildlogs().mkdir(parents=True,exist_ok=True)
  ###########################################
  def genLaunchScript(self,out_path=None,subspace=None):
    numcores = int(os.environ["OBT_NUM_CORES"])

    LAUNCHENV = []
    if self.GIT_SSH_COMMAND!=None:
      LAUNCHENV += ['export GIT_SSH_COMMAND="%s";'%self.GIT_SSH_COMMAND]
    LAUNCHENV += ["obt.env.launch.py"]
    LAUNCHENV += ["--numcores", numcores]
    LAUNCHENV += ["--launch", self.OBT_STAGE]
    LAUNCHENV += ["--prjdir", self.PROJECT_DIR]

    if subspace!= None:
      LAUNCHENV += ["--subspace", subspace]

    LAUNCHENV += [";\n"]

    f = open(str(out_path), 'w')
    f.write(" ".join(obt.command.procargs(LAUNCHENV)))
    f.close()
    os.system("chmod ugo+x %s"%str(out_path))

  ###########################################
  def genBashRc(self,out_path=None,override_sysprompt=None):
    self.log(deco.bright("Generating bashrc override_sysprompt<%s>"%override_sysprompt))
    bdeco = obt.deco.Deco(bash=True)

    HOMEDIR = obt.path.Path(os.environ["HOME"])

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
    if obt.host.IsOsx:    
      SYSPROM = "🍎"
    elif obt.host.IsLinux:    
      SYSPROM = "🐧"

    if "OBT_USE_PROMPT_PREFIX" in os.environ:
      SYSPROM = os.environ["OBT_USE_PROMPT_PREFIX"]

    if override_sysprompt!=None:
      SYSPROM = override_sysprompt

    PROMPT = bdeco.promptL('%s[ %s %s-${OBT_SUBSPACE_PROMPT} ]'%(SYSPROM,stackindic,self.PROJECT_NAME))
    PROMPT += bdeco.promptC("\\w")
    PROMPT += bdeco.promptR("[$(parse_git_branch) ]")
    PROMPT += bdeco.bright("> ")

    validate_prompt(PROMPT)

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
    }

    #########################################
    # dynamic goto and pushd methods
    #  generated from individual deps
    #########################################

    depitems = obt.dep.DepNode.FindWithMethod("env_goto")
    for depitemk in depitems:
      depitem = depitems[depitemk]
      if depitem.supports_host:
        gotos = depitem.env_goto()
        dirs.update(gotos)

    #########################################

    for k in dirs:
        v = dirs[k]
        BASHRC += "obt.goto.%s() { cd %s; };" % (k,v)
        BASHRC += "obt.push.%s() { pushd %s; };" % (k,v)

    ################################################
    # add completions.json from ~/.obt-global/completions.json
    ################################################
  
    OBT_GLOBAL = HOMEDIR/".obt-global"

    if (OBT_GLOBAL/"completions.json").exists():
      json_array = json.load(open(str(OBT_GLOBAL/"completions.json")))
      print(json_array)
      for json_item in json_array:
        BASHRC += "source %s\n" % json_item

    ################################################

    obt_completions_inp = obt.path.obt_bin_priv_base()/"_obt_dep_completions.py"
    for item in ["obt.dep.build.py","obt.dep.info.py","obt.dep.status.py"]:
      completions_line = "complete -C %s %s\n" % (str(obt_completions_inp),item)
      BASHRC += completions_line

    ################################################

    obt_completions_shell_inp = obt.path.obt_bin_priv_base()/"_obt_dep_completions_shell.py"
    completions_line = "complete -C %s obt.dep.shell.py\n" % (str(obt_completions_shell_inp))
    BASHRC += completions_line

    ################################################

    obt_completions_inp = obt.path.obt_bin_priv_base()/"_obt_subspace_completions.py"
    for item in ["obt.subspace.build.py","obt.subspace.launch.py"]:
      completions_line = "complete -C %s %s\n" % (str(obt_completions_inp),item)
      BASHRC += completions_line

    ################################################

    if out_path!=None:
      f = open(str(out_path), 'w')
      f.write(BASHRC)
      f.close()

    return BASHRC
