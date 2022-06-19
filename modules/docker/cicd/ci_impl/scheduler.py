#!/usr/bin/env python3
import jinja2, git, datetime, os, subprocess, argparse, shlex, logging, sys, threading, time
from http import server
from yarl import URL
from pathlib import Path
import badge, uuid, urllib, sqlite3, hashfs, zmq
import orkbb, badge
import _masterimpl

################################################################################

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################
################################################################################
################################################################################
def sched_zmq_thread(sched):
  config = sched.config
  zmq_context = zmq.Context()
  zmq_socket = zmq_context.socket(zmq.REP)
  bindurl = "tcp://%s:%s"%(config.master_bind_addr,config.master_bind_port)
  print("master zmqserver binding to: %s"%bindurl)
  zmq_socket.bind(bindurl)
  poller = zmq.Poller()
  poller.register(zmq_socket, zmq.POLLIN)
  while True:
    if poller.poll(10*1000): # 10s timeout in milliseconds
      message = zmq_socket.recv_json()
      cmd = message["command"]
      workername = message["worker"]
      print( "got cmd<%s> from worker<%s>"%(cmd,workername))
      ##############################################
      if cmd=="worker-connect":
        sched.onWorkerConnect(workername)
        zmq_socket.send_json({
          "connected": True
        })
      ##############################################
      elif cmd=="worker-waiting":
        reply = sched.onWorkerWaiting(workername)
        zmq_socket.send_json(reply);
      ##############################################
      elif cmd=="worker-initializing":
        reply = sched.onWorkerInitializing(workername)
        zmq_socket.send_json(reply);
      ##############################################
      elif cmd=="worker-fetching":
        reply = sched.onWorkerFetching(workername)
        zmq_socket.send_json(reply);
      ##############################################
      elif cmd=="worker-building":
        reply = sched.onWorkerBuilding(workername)
        zmq_socket.send_json(reply);
      ##############################################
      elif cmd=="worker-reporting":
        reply = sched.onWorkerReporting(workername,message)
        zmq_socket.send_json(reply);
      ##############################################
    time.sleep(0.1)
################################################################################
################################################################################
################################################################################

class Scheduler:
  #########################################
  def __init__(self,projectpath,output_dir):
    self.config = _masterimpl.Config(projectpath,output_dir)
    self.workers = self.config.workers
    self.output_dir = output_dir
    self.variants_by_worker = dict()
    self.SRC_TEMPLATEPATH = SCRIPTDIR/"assets"/"index.template"
    self.SRC_LOGOPATH = SCRIPTDIR/"assets"/"OrkidLogo.png"
    self.sitelock = threading.Lock()
    self.schedlock = threading.Lock()
    self.connected_workers = {}
    #######################################
    os.system("cp %s %s"%(self.SRC_LOGOPATH,self.output_path("OrkidLogo.png")))
    os.chdir(output_dir)
    self.update_site(init=True)
    for w in self.variants_by_worker.keys():
      worker = self.config.workers[w]
      worker.start(self)
    #######################################
    self.config.start()
    #######################################
    self.thread = threading.Thread(target=sched_zmq_thread,args=(self,))
    self.thread.start()
  #########################################
  def getWorker(self,workername):
    worker = None
    self.schedlock.acquire(blocking=True)
    if workername in self.workers:
      worker = self.workers[workername]
    self.schedlock.release()
    return worker
  #########################################
  def onWorkerConnect(self,workername):
    worker = self.getWorker(workername)
    if worker!=None:
      self.schedlock.acquire(blocking=True)
      worker.connected = True
      self.connected_workers[workername]=worker
      self.schedlock.release()
  #########################################
  def onWorkerWaiting(self,workername):
    result = {}
    worker = self.getWorker(workername)
    if worker!=None:
      self.updateWorkerRepoData(worker)
      result = worker.onWaiting()
    return result
  #########################################
  def onWorkerInitializing(self,workername):
    result = {}
    worker = self.getWorker(workername)
    if worker!=None:
      result = worker.onInitializing()
    return result
  #########################################
  def onWorkerFetching(self,workername):
    result = {}
    worker = self.getWorker(workername)
    if worker!=None:
      result = worker.onFetching()
    return result
  #########################################
  def onWorkerBuilding(self,workername):
    result = {}
    worker = self.getWorker(workername)
    if worker!=None:
      result = worker.onBuilding()
    return result
  #########################################
  def onWorkerReporting(self,workername,message):
    result = {}
    worker = self.getWorker(workername)
    if worker!=None:
      result = worker.onReporting(message)
    return result
  #########################################
  def onWorkerStatus(self,worker):
    self.update_site(init=False)
  #########################################
  def updateWorkerRepoData(self,worker):
    print("worker<%s> got status<%s>"%(worker.name,worker.status.name))
    self.update_site(init=False)
  #########################################
  def output_path(self,inpath):
    return self.output_dir/inpath
  #########################################
  def load_template(self,name):
    if name == 'index.html':
      with open(self.SRC_TEMPLATEPATH,'r') as f:
        a = f.read()
        return a
    else:
      return "WTF"
  #########################################
  def update_site(self,init=False):
    self.schedlock.acquire(blocking=True)
    variant_list = list()
    self.variants_by_worker = dict()
    for w in self.config.workers.keys():
      self.variants_by_worker[w] = list()
    for vari_key in self.config.variants.keys():
      variant = self.config.variants[vari_key]
      variant.updateRepoData()
      variant_list += [variant]
      #print(variant.name,variant.workers,variant.outputdir)
      for w in variant.workers:
        self.variants_by_worker[w] += [variant]
      if init:
        self.sitelock.acquire(blocking=True)
        os.system("rm -rf %s"%variant.outputdir)
        os.system("mkdir -p %s"%variant.outputdir)
        os.system("touch %s"%(variant.index_html))
        self.sitelock.release()
      #################################
      b = badge.Data()
      b._outpath = variant.status_svg
      b.updateStatus(variant.curbuildstatus,variant.prvbuildstatus)
      self.sitelock.acquire(blocking=True)
      b.create()
      self.sitelock.release()
    ################################################################################
    # templating engine
    ################################################################################
    env = jinja2.Environment(
        loader=jinja2.FunctionLoader(self.load_template),
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    template = env.get_template('index.html')
    output = template.render(MASTERNAME=self.config.master_name,VARIANT_LIST=variant_list )
    self.sitelock.acquire(blocking=True)
    with open(self.output_dir/"index.html",'w') as f:
      f.write(output)
    self.sitelock.release()
    self.schedlock.release()
  #########################################
