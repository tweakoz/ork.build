import sys, os, re, json, argparse, re, shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom

####################################################################

def find_executable(exec_name):
  """Find the executable in PATH or use the provided path."""
  exec_name = os.path.expandvars(exec_name)
  if exec_name.startswith(("./", "../")) or os.path.isabs(exec_name):
    full_path = os.path.abspath(exec_name)
    if os.path.exists(full_path) and os.access(full_path, os.X_OK):
      return full_path
    return None
  for path in os.environ["PATH"].split(os.pathsep):
    full_path = os.path.join(path, exec_name)
    if os.path.exists(full_path) and os.access(full_path, os.X_OK):
      return full_path
  if os.path.exists(exec_name) and os.access(exec_name, os.X_OK):
    return exec_name
  return None

####################################################################

def is_python_script(executable_path):
  """Determine if the given file is a Python script."""
  try:
    with open(executable_path, 'r') as f:
      first_line = f.readline().strip()
      return first_line.startswith("#!") and "python" in first_line
  except Exception as e:
    return False

####################################################################

def orkid_debug_env_vars():
  vars = {
    "ORKID_WORKSPACE_DIR": os.getenv("ORKID_WORKSPACE_DIR"),
    "LD_LIBRARY_PATH": os.getenv("LD_LIBRARY_PATH"),
    "PATH": os.getenv("PATH"),
    "PYTHONPATH": os.getenv("PYTHONPATH"),
    "OBT_STAGE": os.getenv("OBT_STAGE"),
    "ORKID_LEV2_EXAMPLES_DIR": os.getenv("ORKID_LEV2_EXAMPLES_DIR"),
  }
  if "ORKID_GRAPHICS_API" in os.environ:
    vars["ORKID_GRAPHICS_API"] = os.getenv("ORKID_GRAPHICS_API")
  return vars

####################################################################

def xml_prettify(elem):
  """Return a pretty-printed XML string for the Element."""
  rough_string = ET.tostring(elem, 'utf-8')
  reparsed = minidom.parseString(rough_string)
  return reparsed.toprettyxml(indent="  ")

####################################################################

def create_xcode_structure(workspace_path, dap, env_vars, working_dir=None):
  exec_name = dap.executable_name
  bin_path = dap.executable_path
  exec_args = dap.executable_args
  # Remove existing workspace if it exists
  if os.path.exists(workspace_path):
    shutil.rmtree(workspace_path)

  # Create directories
  shared_data_path = os.path.join(workspace_path, "xcshareddata")
  shared_schemes_path = os.path.join(shared_data_path, "xcschemes")

  for directory in [workspace_path, shared_data_path, shared_schemes_path]:
    os.makedirs(directory, exist_ok=True)

  # Create contents.xcworkspacedata
  workspace_content = ET.Element("Workspace", version="1.0")
  workspace_file = os.path.join(workspace_path, 'contents.xcworkspacedata')
  with open(workspace_file, 'w') as f:
    f.write(xml_prettify(workspace_content))

  # Generate .xcscheme file
  scheme_name = os.path.basename(bin_path)
  scheme_file = os.path.join(shared_schemes_path, f'{scheme_name}.xcscheme')
  scheme_content = ET.Element("Scheme", LastUpgradeVersion="1500", version="1.7")

  launch_action = ET.SubElement(scheme_content, "LaunchAction",
                                buildConfiguration="Debug",
                                selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB",
                                selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB",
                                launchStyle="0", 
                                useCustomWorkingDirectory="YES" if (working_dir!=None) else "NO",
                                ignoresPersistentStateOnLaunch="NO",
                                debugDocumentVersioning="YES", debugServiceExtension="internal",
                                allowLocationSimulation="YES")

  if working_dir!=None:
    launch_action.set('customWorkingDirectory', working_dir)

  path_runnable = ET.SubElement(launch_action, "PathRunnable", runnableDebuggingMode="0", FilePath=bin_path)

  env_vars_elem = ET.SubElement(launch_action, "EnvironmentVariables")
  for key, value in env_vars.items():
    if value:
      ET.SubElement(env_vars_elem, "EnvironmentVariable", key=key, value=value, isEnabled="YES")

  # Integrate exec_args into the scheme
  ET.SubElement(launch_action, "CommandLineArguments").extend(
    [ET.Element("CommandLineArgument", argument=arg, isEnabled="YES") for arg in exec_args]
  )

  with open(scheme_file, 'w') as f:
    f.write(xml_prettify(scheme_content))

  os.system(f"open {workspace_path}")
  
  
class DebugArgParser:
  #########################################
  def __init__(self):
    self.executable_name = sys.argv[1]
    if len(sys.argv) > 2:
      self.executable_args = sys.argv[2:]
    else:
      self.executable_args = []
    self._compute()
    #exe_path, exe_args, exe_name = get_exec_and_args(args)
  #########################################
  def _compute(self):
    self.executable_path = find_executable(self.executable_name)

    if not self.executable_path:
      print(f"Executable '{self.executable_name}' not found in $PATH.")
      exit(1)

    if is_python_script(self.executable_path):
      python_path = find_executable("python3")
      if not python_path:
        print("python3 not found.")
        exit(1)
      self.executable_args.insert(0, self.executable_path)
      self.executable_path = os.path.realpath(python_path)

    self.exec_name = re.sub(r"[^a-zA-Z0-9]", "_", self.executable_name)
    #return executable_path, executable_args, exec_name

  #########################################

#env_vars = dh.orkid_debug_env_vars()
