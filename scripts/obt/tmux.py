from obt import command
class Session(object):
  #########################################
  def __init__(self, session_name, orientation="horizontal"):
    self.session_name = session_name
    self.orientation = orientation
    self.cmd_new_session = [
      "tmux", "new-session",
      "-d", "-s", f"{self.session_name}"]
    if self.orientation == "vertical":
      self.cmd_add_session = [
        "tmux", "split-window",
        "-v", "-t", f"{self.session_name}"]
      self.cmd_select_layout = [
        "tmux", "select-layout",
        "-t", f"{self.session_name}:0",
        "even-vertical"
      ]
    elif self.orientation == "horizontal":
      self.cmd_add_session = [
        "tmux", "split-window",
        "-h", "-t", f"{self.session_name}"]
      self.cmd_select_layout = [
        "tmux", "select-layout",
        "-t", f"{self.session_name}:0",
        "even-horizontal"
      ]
    self.cmd_attach_session = [
      "tmux", "attach-session",
      "-t", f"{self.session_name}"
    ]
    self.cmd_chain = command.chain2(do_log=True)
  #########################################
  def first_command(self, cmd):
    self.cmd_chain.add(self.cmd_new_session + cmd)
  #########################################
  def next_command(self, cmd):
    self.cmd_chain.add(self.cmd_add_session + cmd)
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
    self.select_layout()
    self.attach_session()
    self.cmd_chain.execute()
    return self.cmd_chain.ok()