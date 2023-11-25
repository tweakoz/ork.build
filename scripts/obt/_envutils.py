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
  def __init__(self,config):
    assert(config.valid)
    self._config = config

  ###########################################
  def log(self,x):
    if not self._config.quiet:
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
    # create symlink to default python
    if not (obt.path.prefix()/"bin/python").exists():
      if obt.host.IsOsx:
        if obt.host.IsAppleSilicon:
          os.system("ln -s /opt/local/bin/python3 %s" % str(obt.path.prefix()/"bin/os-python"))
        else:
          os.system("ln -s /usr/local/bin/python3 %s" % str(obt.path.prefix()/"bin/os-python"))
      else:
        os.system("ln -s /usr/bin/python3 %s" % str(obt.path.prefix()/"bin/os-python"))

  ###########################################
  def genLaunchScript(self,out_path=None,subspace=None):
    numcores = int(os.environ["OBT_NUM_CORES"])

    LAUNCHENV = []
    if self._config._git_ssh_command!=None:
      LAUNCHENV += ['export GIT_SSH_COMMAND="%s";'%self._config._git_ssh_command]

    if self._config.inplace:
      LAUNCHENV += [str(self._config.bin_pub_dir/"obt.env.launch.py")]
      LAUNCHENV += ["--inplace"]
    else:
      LAUNCHENV += ["obt.env.launch.py"]

    LAUNCHENV += ["--numcores", numcores]
    LAUNCHENV += ["--stagedir", self._config.stage_dir]
    LAUNCHENV += ["--project", self._config.project_dir]

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

    PROMPT = bdeco.promptL('%s[ %s %s-${OBT_SUBSPACE_PROMPT} ]'%(SYSPROM,stackindic,self._config.project_name))
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
