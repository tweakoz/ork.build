"""obt.net.controller — the obtnet controller: node registry + control relay
+ aggregated fleet event stream.

O1 architecture (replaces the v0 blocking REP):
  control (ROUTER, :7461) — clients and nodes speak plain REQ, unchanged on
      the wire. Fast ops (connect/ping/list/controller_info) answer inline on
      the main loop; RELAY ops dispatch to a small thread pool, replies flow
      back through an inproc PUSH/PULL so the ROUTER (single-owner) sends
      them. A long relayed run no longer delays anyone's heartbeat.
  events (PUB, :7462) — re-publishes every node's event stream (the watch
      verb subscribes here) + controller's own connect/disconnect events.
      The proxy thread owns a SUB connected to each node's PUB (endpoints
      arrive via a queue at Connect; stale endpoints from node restarts are
      harmless zmq reconnect noise, bounded by fleet size).
Timesync: ping replies carry t1 (recv) + t2 (send); the NODE computes the
NTP-style offset and reports it in its next ping — the registry just displays.
Bulk NEVER relays through here: clients chunk-fetch straight from node fetch
sockets (the registry hands out addresses).
"""

import os
import queue
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import zmq

from obt.net import proto


class NodeRecord:
    def __init__(self, name, uuid, ip, msg):
        self.name = name
        self.uuid = uuid
        self.ip = ip
        self.addr = f"tcp://{ip}:{msg['control_port']}"
        self.pub_addr = f"tcp://{ip}:{msg['pub_port']}"
        self.fetch_addr = f"tcp://{ip}:{msg['fetch_port']}"
        self.capabilities = msg.get("capabilities", {})
        self.connected_at = proto.now()
        self.last_ping = proto.now()
        self.load = 0.0
        self.n_jobs = 0
        self.clock_offset_ms = None
        self.rtt_ms = None

    def to_dict(self):
        return {"name": self.name, "uuid": self.uuid, "addr": self.addr,
                "fetch_addr": self.fetch_addr, "pub_addr": self.pub_addr,
                "capabilities": self.capabilities, "load": self.load,
                "n_jobs": self.n_jobs,
                "clock_offset_ms": self.clock_offset_ms, "rtt_ms": self.rtt_ms,
                "last_ping_age_s": round(proto.now() - self.last_ping, 2)}


class Controller:
    # ops relayed verbatim to the target node (msg must carry "node")
    RELAY_OPS = (proto.OP_RUN_COMMAND, proto.OP_NODE_INFO,
                 proto.OP_UPLOAD_QUERY, proto.OP_UPLOAD_FILE,
                 proto.OP_JOB_SUBMIT, proto.OP_JOB_STATUS, proto.OP_JOB_LIST,
                 proto.OP_JOB_CANCEL, proto.OP_JOB_LOG)

    def __init__(self, port: int = proto.CONTROLLER_PORT,
                 pub_port: int = proto.CONTROLLER_PUB_PORT):
        self.port = port
        self.pub_port = pub_port
        self.ctx = zmq.Context.instance()
        self.nodes = {}                 # name -> NodeRecord
        self.nodes_lock = threading.Lock()
        self._stop = threading.Event()
        self.control = self.ctx.socket(zmq.ROUTER)
        self.control.setsockopt(zmq.LINGER, 0)
        self.control.bind(f"tcp://0.0.0.0:{port}")
        # worker replies re-enter the main loop here (ROUTER is single-owner)
        self._reply_pull = self.ctx.socket(zmq.PULL)
        self._reply_pull.bind("inproc://obtnet.replies")
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="relay")
        # event proxy plumbing (the proxy thread owns SUB + PUB)
        self._sub_endpoints = queue.Queue()   # new node pub addrs to subscribe
        self._ctl_events = queue.Queue()      # controller-authored events

    # -- node-facing (main loop, fast) ---------------------------------------
    def _h_connect(self, msg):
        ip = msg.get("advertise_ip") or "127.0.0.1"
        rec = NodeRecord(msg["name"], msg["uuid"], ip, msg)
        with self.nodes_lock:
            replaced = msg["name"] in self.nodes
            self.nodes[msg["name"]] = rec
        self._sub_endpoints.put(rec.pub_addr)
        line = (f"node {'re' if replaced else ''}connected: {rec.name} @ {rec.addr} "
                f"({rec.capabilities.get('os','?')}/{rec.capabilities.get('arch','?')}"
                f"{' gpu=' + rec.capabilities['gpu'] if 'gpu' in rec.capabilities else ''})")
        print(f"[obtnet.controller] {line}", flush=True)
        self._ctl_events.put(proto.make_event("controller", "node_connect", line,
                                              node_name=rec.name))
        return proto.make_reply_ok(controller_epoch=proto.now())

    def _h_ping(self, msg, t1):
        rec = None
        with self.nodes_lock:
            for r in self.nodes.values():
                if r.uuid == msg.get("uuid"):
                    rec = r; break
        if rec is None:
            return proto.make_reply_err(proto.ERR_UNKNOWN_NODE)  # node will re-Connect
        rec.last_ping = t1
        rec.load = msg.get("load", 0.0)
        rec.n_jobs = msg.get("n_jobs", 0)
        if msg.get("clock_offset_ms") is not None:
            rec.clock_offset_ms = msg["clock_offset_ms"]
            rec.rtt_ms = msg.get("rtt_ms")
        return proto.make_reply_ok(t0=msg["t0"], t1=t1, t2=proto.now())

    # -- client-facing (main loop, fast) --------------------------------------
    EXPIRE_S = 120   # heartbeat is 0.5s; anything this stale is gone, not busy

    def _h_list_nodes(self, msg):
        with self.nodes_lock:
            cutoff = proto.now() - self.EXPIRE_S
            for name in [n for n, r in self.nodes.items() if r.last_ping < cutoff]:
                del self.nodes[name]
                print(f"[obtnet.controller] node expired: {name}", flush=True)
            return proto.make_reply_ok(nodes=[r.to_dict() for r in self.nodes.values()])

    def _h_controller_info(self, msg):
        with self.nodes_lock:
            n = len(self.nodes)
        return proto.make_reply_ok(pub_port=self.pub_port, nodes=n,
                                   epoch=proto.now(), pid=os.getpid())

    # -- relay (thread pool) ---------------------------------------------------
    def _relay_task(self, ident, msg):
        """Worker thread: one-shot REQ to the node, reply via inproc PUSH."""
        name = msg.get("node")
        with self.nodes_lock:
            rec = self.nodes.get(name)
        if rec is None:
            with self.nodes_lock:
                known = sorted(self.nodes)
            reply = proto.make_reply_err(proto.ERR_UNKNOWN_NODE, node=name, known=known)
        else:
            timeout_ms = int((float(msg.get("timeout_s", 300)) + 10) * 1000)
            s = self.ctx.socket(zmq.REQ)
            s.setsockopt(zmq.LINGER, 0)
            s.setsockopt(zmq.RCVTIMEO, timeout_ms)
            s.setsockopt(zmq.SNDTIMEO, 5000)
            try:
                s.connect(rec.addr)
                fwd = dict(msg); fwd.pop("node", None)
                s.send(proto.make_request(fwd.pop("op"),
                                          **{k: v for k, v in fwd.items() if k != "v"}))
                reply = s.recv()     # already an envelope — pass through verbatim
            except zmq.error.Again:
                reply = proto.make_reply_err(proto.ERR_RELAY_TIMEOUT, node=name)
            finally:
                s.close()
        push = self.ctx.socket(zmq.PUSH)
        push.setsockopt(zmq.LINGER, 1000)
        try:
            push.connect("inproc://obtnet.replies")
            push.send_multipart([ident, reply])
        finally:
            push.close()

    # -- event proxy (own thread; owns SUB + PUB) -------------------------------
    def _event_proxy_loop(self):
        sub = self.ctx.socket(zmq.SUB)
        sub.setsockopt(zmq.LINGER, 0)
        sub.setsockopt_string(zmq.SUBSCRIBE, "")
        pub = self.ctx.socket(zmq.PUB)
        pub.setsockopt(zmq.LINGER, 0)
        pub.bind(f"tcp://0.0.0.0:{self.pub_port}")
        poller = zmq.Poller()
        poller.register(sub, zmq.POLLIN)
        connected = set()
        while not self._stop.is_set():
            while True:                       # absorb new node pub endpoints
                try:
                    ep = self._sub_endpoints.get_nowait()
                except queue.Empty:
                    break
                if ep not in connected:
                    sub.connect(ep)
                    connected.add(ep)
            while True:                       # controller-authored events
                try:
                    pub.send(self._ctl_events.get_nowait())
                except queue.Empty:
                    break
            if dict(poller.poll(timeout=250)):
                pub.send(sub.recv())          # forward verbatim
        sub.close(); pub.close()

    # -- main loop ----------------------------------------------------------
    def run(self):
        print(f"[obtnet.controller] control tcp://*:{self.port} "
              f"events tcp://*:{self.pub_port}", flush=True)
        proxy = threading.Thread(target=self._event_proxy_loop, daemon=True)
        proxy.start()
        poller = zmq.Poller()
        poller.register(self.control, zmq.POLLIN)
        poller.register(self._reply_pull, zmq.POLLIN)
        while not self._stop.is_set():
            socks = dict(poller.poll(timeout=250))
            if self._reply_pull in socks:
                ident, reply = self._reply_pull.recv_multipart()
                self.control.send_multipart([ident, b"", reply])
            if self.control not in socks:
                continue
            frames = self.control.recv_multipart()
            ident, payload = frames[0], frames[-1]
            t_recv = proto.now()
            try:
                msg = proto.parse_message(payload)
                op = msg.get("op")
                if op == proto.OP_CONNECT:
                    reply = self._h_connect(msg)
                elif op == proto.OP_PING:
                    reply = self._h_ping(msg, t_recv)
                elif op == proto.OP_LIST_NODES:
                    reply = self._h_list_nodes(msg)
                elif op == proto.OP_CONTROLLER_INFO:
                    reply = self._h_controller_info(msg)
                elif op in self.RELAY_OPS and "node" in msg:
                    self._pool.submit(self._relay_task, ident, msg)
                    continue                 # reply arrives via _reply_pull
                else:
                    reply = proto.make_reply_err(proto.ERR_UNKNOWN_OP, op=op)
            except Exception as e:
                reply = proto.make_reply_err(proto.ERR_EXEC_FAILED, detail=repr(e))
            self.control.send_multipart([ident, b"", reply])

    def stop(self):
        self._stop.set()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="obtnet controller")
    ap.add_argument("--port", type=int, default=proto.CONTROLLER_PORT)
    ap.add_argument("--pub-port", type=int, default=proto.CONTROLLER_PUB_PORT)
    args = ap.parse_args(argv)
    controller = Controller(port=args.port, pub_port=args.pub_port)
    signal.signal(signal.SIGTERM, lambda *a: controller.stop())
    try:
        controller.run()
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()
