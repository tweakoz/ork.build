from obt import command

class Session(object):
  #########################################
  def __init__(self, session_name, orientation="horizontal",working_dir=None,kill_first=True):
    self.session_name = session_name
    self.orientation = orientation
    self.working_dir = working_dir
    self.kill_first = kill_first
    self.cmd_new_session = [
      "tmux", "new-session",
      "-d", "-s", f"{self.session_name}"]
    if self.orientation == "vertical":
      self.cmd_add_session = [
        "tmux", "split-window",
        "-v", "-t", f"{self.session_name}"]
      self.cmd_select_layout = [
        "tmux", "select-layout",
        "-t", f"{self.session_name}",
        "even-vertical"
      ]
    elif self.orientation == "horizontal":
      self.cmd_add_session = [
        "tmux", "split-window",
        "-h", "-t", f"{self.session_name}"]
      self.cmd_select_layout = [
        "tmux", "select-layout",
        "-t", f"{self.session_name}",
        "even-horizontal"
      ]
    self.cmd_attach_session = [
      "tmux", "attach-session",
      "-t", f"{self.session_name}"
    ]
    self.kill_session = [
      "tmux", "kill-session",
      "-t", f"{self.session_name}"
    ]
    if working_dir!=None:
      self.cmd_new_session.append("-c")
      self.cmd_new_session.append(working_dir)
      self.cmd_add_session.append("-c")
      self.cmd_add_session.append(working_dir)

    self.cmd_chain = command.chain2(do_log=True)
    self.post_chain = list()
    self.num_panes = 1  # Start with 1 since new-session creates the first pane
    
    ######################
    # default key bindings
    ######################
    self.bind_key("K", "kill-session", table="prefix")
    self.bind_key("H", "select-layout even-horizontal", table="prefix")
    self.bind_key("V", "select-layout even-vertical", table="prefix")

  #########################################
  def bind_zoom_panes(self):
    """Bind Shift+1 through Shift+num_panes to zoom respective panes"""
    # Map shift+number to actual characters sent
    shift_numbers = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
    
    for i in range(min(self.num_panes, len(shift_numbers))):
        key = shift_numbers[i]  # !, @, #, $, etc.
        cmd = f"resize-pane -Z -t {self.session_name}.{i}"
        self.bind_key_raw(key, cmd, table="prefix")
        
  #########################################
  def bind_key_raw(self, key=None, cmd=None, table="prefix"):
    """Bind a key to a raw command without modification"""
    assert(key is not None and cmd is not None)
    cmd_parts = cmd.split() if isinstance(cmd, str) else cmd
    self.post_chain.append([
      "tmux", "bind-key",
      "-T", table,
      key] + cmd_parts)

  #########################################
  def bind_key(self, key=None, cmd=None, table="prefix" ):
    """Bind a key to a command in the tmux session."""
    assert( key is not None and cmd is not None )
    # Handle commands with arguments (like select-layout even-vertical)
    if isinstance(cmd, list):
      cmd_parts = cmd
    else:
      cmd_parts = cmd.split()

    # For select-layout, we need to insert -t session_name before the layout name
    if len(cmd_parts) >= 2 and cmd_parts[0] == "select-layout":
      cmd_with_target = [cmd_parts[0], "-t", f"{self.session_name}"] + cmd_parts[1:]
    else:
      cmd_with_target = cmd_parts + ["-t", f"{self.session_name}"]

    self.post_chain.append([
      "tmux", "bind-key",
      "-T", table,
      key] + cmd_with_target)
      
  #########################################
  def kill(self):
    try:
      command.run(self.kill_session, check=False)
    except:
      pass
      
  #########################################
  def first_command(self, cmd):
    self.cmd_chain.add(self.cmd_new_session + cmd)
    
  #########################################
  def next_command(self, cmd):
    self.cmd_chain.add(self.cmd_add_session + cmd)
    self.num_panes += 1  # Increment when we actually add a pane
    
  #########################################
  def command(self, cmd):
    if self.cmd_chain.count == 0:
      self.first_command(cmd)
    else:
      self.next_command(cmd)
      
  #########################################
  def select_layout(self):
    self.cmd_chain.add(self.cmd_select_layout)
    
  #########################################
  def attach_session(self):
    self.cmd_chain.add(self.cmd_attach_session)
    
  #########################################
  def execute(self):
    self.bind_zoom_panes()
    ########################
    if self.kill_first:
      self.kill()
    ########################
    for item in self.post_chain:
      self.cmd_chain.add(item)
    ########################
    self.select_layout()
    self.attach_session()
    ########################
    OK = (self.cmd_chain.execute() == 0)
    return OK