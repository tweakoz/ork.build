#!/usr/bin/env python3
import jinja2, git, datetime, os, subprocess, argparse, shlex, logging, sys, threading, time
from http import server
from yarl import URL
from pathlib import Path
import uuid, urllib

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################

def HandlerClass(OUTPUTDIR,SITELOCK):
  class handlerclass(server.SimpleHTTPRequestHandler):
      ###############################################################
      server_version = "yo"
      sys_version = "what up"
      _OUTPUTDIR = OUTPUTDIR
      _SITELOCK = SITELOCK
      ###############################################################
      def __init__(self,req,client_addr,server):
       self.outputdir = handlerclass._OUTPUTDIR
       self.sitelock = handlerclass._SITELOCK
       self.errtext = "YO".encode("UTF-8")
       super(handlerclass, self).__init__(req,client_addr,server)
      ###############################################################
      def send_my_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("ETag", '"'+str(uuid.uuid4())+'"')
      ###############################################################
      def end_headers(self):
        self.send_my_headers()
        server.SimpleHTTPRequestHandler.end_headers(self)
      ###############################################################
      def do_ERROR(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", len(self.errtext))
        self.end_headers()
        self.wfile.write(self.errtext)
      ###############################################################
      def translate_path(self, path):
        path = path.strip("/")
        print("inppath<%s>"%(path))
        if path == "":
          path = "index.html"
        elif False==os.path.isfile(self.outputdir/path):
          path = "ERROR"
        qualifiedurl = self.outputdir/path
        print("path<%s> qual<%s>"%(path,qualifiedurl))
        return str(qualifiedurl)
      ###############################################################
      def do_GET(self):
        rval = None
        self.sitelock.acquire(blocking=True)
        referer = self.headers.get('Referer')
        print("Referer<%s> path<%s>"%(referer,self.path))
        self.path = self.path.strip("/")
        if self.path == "":
          self.path = "index.html"
        if os.path.isfile(self.outputdir/self.path):
          rval = server.SimpleHTTPRequestHandler.do_GET(self)
        else:
          rval = None
          self.do_ERROR()
        self.sitelock.release()
        return rval
      ###############################################################
  return handlerclass
