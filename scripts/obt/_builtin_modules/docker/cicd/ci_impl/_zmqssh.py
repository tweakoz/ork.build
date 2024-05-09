import zmq
from zmq import ssh
from sshtunnel import SSHTunnelForwarder
################################################################################
################################################################################
class ZmqSsh1:
  def __init__(self,ipaddr=None,user=None,key=None,lbindaddr=None):
    self.zmq_url = "tcp://%s:%s"%(lbindaddr[0],lbindaddr[1])
    self.zmq_context = zmq.Context()
    self.zmq_socket = self.zmq_context.socket(zmq.REQ)
    sshspec = "%s@%s" % (user,ipaddr)
    #print("zmqurl: %s"%self.zmq_url)
    #print("sshspec: %s"%sshspec)
    ssh.tunnel_connection(self.zmq_socket, self.zmq_url, sshspec, keyfile=key, timeout=30)
    self.zmq_socket.connect(self.zmq_url)
    self.zmq_socket.setsockopt(zmq.LINGER, 0)
    self.poller = None
  def __enter__(self):
    self.poller = zmq.Poller()
    self.poller.register(self.zmq_socket, zmq.POLLIN)
    return self
  def __exit__(self, type, value, traceback):
    self.zmq_socket.close()
    self.zmq_socket = None
    self.zmq_context = None
  def send_json(self,jsonval):
    self.zmq_socket.send_json(jsonval)
  def recv_json(self,timeout=10):
    rval = None
    if timeout!=None:
      timeout = timeout*1000
    if self.poller.poll(timeout): # 10s timeout in milliseconds
      rval = self.zmq_socket.recv_json()
    return rval
################################################################################
################################################################################
class ZmqSsh2:
  def __init__(self,ipaddr=None,user=None,key=None,lbindaddr=None):
    self.tunnel = SSHTunnelForwarder(
      ipaddr,
      ssh_username=user,
      ssh_pkey=key,
      remote_bind_address=lbindaddr
    )
    self.tunnel.start()
    self.tunnelled_port = self.tunnel.local_bind_port
    #print(self.tunnelled_port)
    self.zmq_url = "tcp://127.0.0.1:%s"%(self.tunnelled_port)
    self.zmq_context = zmq.Context()
    self.zmq_socket = self.zmq_context.socket(zmq.REQ)
    self.zmq_socket.connect(self.zmq_url)
  def __enter__(self):
    self.poller = zmq.Poller()
    self.poller.register(self.zmq_socket, zmq.POLLIN)
    return self
  def __exit__(self, type, value, traceback):
    self.zmq_socket.close()
    self.zmq_socket = None
    self.zmq_context = None
    if self.tunnel!=None:
      self.tunnel.close()
  def send_json(self,jsonval):
    self.zmq_socket.send_json(jsonval)
  def recv_json(self,timeout=10):
    rval = None
    if timeout!=None:
      timeout = timeout*1000
    if self.poller.poll(timeout): # 10s timeout in milliseconds
      rval = self.zmq_socket.recv_json()
    return rval
################################################################################
################################################################################
class Direct:
  def __init__(self,ipaddr=None,user=None,key=None,lbindaddr=None):
    self.zmq_url = "tcp://%s:%s"%(lbindaddr[0],lbindaddr[1])
    print("CONNECTING to master @ %s"%self.zmq_url)
    self.zmq_context = zmq.Context()
    self.zmq_socket = self.zmq_context.socket(zmq.REQ)
    self.zmq_socket.connect(self.zmq_url)
    print("CONNECTED %s"%self.zmq_socket)
  def __enter__(self):
    self.poller = zmq.Poller()
    self.poller.register(self.zmq_socket, zmq.POLLIN)
    return self
  def __exit__(self, type, value, traceback):
    self.zmq_socket.close()
    self.zmq_socket = None
    self.zmq_context = None
    if hasattr(self,"tunnel") and (self.tunnel!=None):
      self.tunnel.close()
  def send_json(self,jsonval):
    self.zmq_socket.send_json(jsonval)
  def recv_json(self,timeout=10):
    rval = None
    if timeout!=None:
      timeout = timeout*1000
    if self.poller.poll(timeout): # 10s timeout in milliseconds
      rval = self.zmq_socket.recv_json()
    return rval