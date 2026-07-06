"""obt.net.proto — wire protocol for obtnet (controller/node distributed execution).

v2 (O1, 2026-07-05): versioned JSON envelope over zmq. Adds async jobs
(submit/status/list/cancel/log + FSM states), the PUB event stream, chunked
artifact fetch (the download_artifacts verb — bulk NEVER rides the control
socket), and heartbeat timesync fields.

Every message is one zmq frame of UTF-8 JSON carrying "v": PROTO_VERSION.
Requests carry "op"; replies carry "ok": true/false (+ "error" on false).
Events (PUB) carry "ev" and are fire-and-forget (the node's on-disk job
record is the durable truth; PUB is best-effort).
"""

import json
import os
import socket
import time
import uuid as _uuid

PROTO_VERSION = 2

# default ports (controller binds these; nodes bind ephemeral + report at connect)
CONTROLLER_PORT = 7461        # ROUTER control
CONTROLLER_PUB_PORT = 7462    # aggregated fleet event stream (watch verb)

# ---------------------------------------------------------------------------
# op constants
# ---------------------------------------------------------------------------

OP_CONNECT      = "connect"        # node -> controller: register {name, ports, caps}
OP_PING         = "ping"           # node -> controller heartbeat + timesync carrier
OP_LIST_NODES  = "list_nodes"    # client -> controller
OP_CONTROLLER_INFO = "controller_info"  # client -> controller {pub_port, ...}
OP_NODE_INFO   = "node_info"     # client -> controller (relayed) or -> node direct
OP_RUN_COMMAND  = "run_command"    # client -> controller {node, ...} (relayed) — SYNC path
OP_UPLOAD_QUERY = "upload_query"   # client -> controller {node, sha256} (relayed)
OP_UPLOAD_FILE  = "upload_file"    # client -> controller {node, sha256, bytes_b64} (relayed)
OP_JOB_SUBMIT   = "job_submit"     # client -> node (relayed): async job -> {job}
OP_JOB_STATUS   = "job_status"     # client -> node (relayed): {job} -> state dict
OP_JOB_LIST     = "job_list"       # client -> node (relayed): recent jobs
OP_JOB_CANCEL   = "job_cancel"     # client -> node (relayed): SIGTERM the pgid
OP_JOB_LOG      = "job_log"        # client -> node (relayed): bounded tail/grep of a log
OP_FETCH_CHUNK  = "fetch_chunk"    # client -> node FETCH socket (direct, chunked)
# tree.sync ops — ALL on the node FETCH socket (bulk lane, direct, no relay):
OP_BLOB_PUT     = "blob_put"       # chunked upload into the node cache (resumable)
OP_TREE_MANIFEST = "tree_manifest" # walk+hash a remote dir -> manifest
OP_TREE_APPLY   = "tree_apply"     # materialize manifest entries from cache

# job FSM states (terminal = DONE/FAILED/TIMEOUT/CANCELLED)
JOB_QUEUED    = "queued"
JOB_RUNNING   = "running"
JOB_DONE      = "done"        # process ran to completion (rc may be nonzero)
JOB_FAILED    = "failed"      # could not exec / infrastructure error
JOB_TIMEOUT   = "timeout"
JOB_CANCELLED = "cancelled"
JOB_TERMINAL  = (JOB_DONE, JOB_FAILED, JOB_TIMEOUT, JOB_CANCELLED)

# error reasons (structured, greppable)
ERR_UNKNOWN_OP     = "unknown_op"
ERR_BAD_VERSION    = "bad_version"
ERR_UNKNOWN_NODE  = "unknown_node"
ERR_UNKNOWN_JOB    = "unknown_job"
ERR_UNKNOWN_SHA    = "unknown_sha"
ERR_UNKNOWN_KIND   = "unknown_kind"
ERR_RELAY_TIMEOUT  = "relay_timeout"
ERR_EXEC_FAILED    = "exec_failed"
ERR_TIMEOUT        = "timeout"

# payload caps. Sync run_command keeps inline caps; ASYNC job outputs always go
# to the node's content-addressed cache and travel via chunked fetch (no caps).
MAX_STDOUT_BYTES  = 1 << 20        # 1 MB (sync path + status tails)
MAX_STDERR_BYTES  = 256 << 10      # 256 KB
MAX_INLINE_OUTPUT = 4 << 20        # 4 MB per sync-path output file
MAX_INLINE_UPLOAD = 16 << 20       # 16 MB per upload frame (LAN)
FETCH_CHUNK_BYTES = 4 << 20        # raw bytes per fetch_chunk reply
LOG_TAIL_MAX_BYTES = 256 << 10     # bounded job_log reads

def normalize_controller_addr(addr):
    """Accept lazy controller addresses: '192.168.1.50', 'buildbox:7461',
    'tcp://192.168.1.50' — all normalize to 'tcp://host:port' with the
    default port (7461) filled in when omitted."""
    addr = addr.strip()
    if "://" not in addr:
        addr = "tcp://" + addr
    scheme, rest = addr.split("://", 1)
    if ":" not in rest:
        rest = f"{rest}:{CONTROLLER_PORT}"
    return f"{scheme}://{rest}"

# ---------------------------------------------------------------------------
# envelope helpers
# ---------------------------------------------------------------------------

def make_request(op, **fields):
    return json.dumps({"v": PROTO_VERSION, "op": op, **fields}).encode("utf-8")

def make_reply_ok(**fields):
    return json.dumps({"v": PROTO_VERSION, "ok": True, **fields}).encode("utf-8")

def make_reply_err(error, **fields):
    return json.dumps({"v": PROTO_VERSION, "ok": False, "error": error, **fields}).encode("utf-8")

def make_event(node, ev, line, **fields):
    """PUB frame. `line` is the preformatted human string — watch prints exactly
    what the node console shows (one UI, two viewports)."""
    return json.dumps({"v": PROTO_VERSION, "t": now(), "node": node, "ev": ev,
                       "line": line, **fields}).encode("utf-8")

def parse_message(data):
    msg = json.loads(data.decode("utf-8"))
    if msg.get("v") != PROTO_VERSION:
        raise ValueError(f"{ERR_BAD_VERSION}: got {msg.get('v')} want {PROTO_VERSION}")
    return msg

# ---------------------------------------------------------------------------
# identity / capabilities
# ---------------------------------------------------------------------------

def new_uuid64():
    return _uuid.uuid4().int & 0xFFFFFFFFFFFFFFFF

def new_job_id():
    return "j-" + _uuid.uuid4().hex[:8]

def probe_capabilities():
    """Best-effort machine capabilities dict (advertised at Connect)."""
    caps = {
        "hostname": socket.gethostname(),
        "os": os.uname().sysname,
        "arch": os.uname().machine,
        "pid": os.getpid(),
    }
    try:
        caps["load"] = os.getloadavg()[0]
    except OSError:
        pass
    try:  # obt staging, when inside an obt env
        stage = os.environ.get("OBT_STAGE")
        if stage:
            caps["obt_stage"] = stage
    except Exception:
        pass
    # GPU probe (best-effort, non-fatal)
    try:
        import subprocess
        r = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                           capture_output=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            caps["gpu"] = r.stdout.decode().strip().splitlines()[0]
    except Exception:
        pass
    return caps

def now():
    return time.time()


class ClockSync:
    """NTP-style offset estimate from heartbeat stamps. Node sends t0, controller
    stamps t1 (recv) + t2 (send), node stamps t3 (reply recv):
        offset = ((t1 - t0) + (t2 - t3)) / 2      rtt = (t3 - t0) - (t2 - t1)
    Keep a sliding window; trust the sample with the smallest rtt (least queueing
    noise). Good to ~ms on LAN — enough for job-timeline correlation, not for
    realtime (that's orknet's 4-stamp filtered mapping)."""

    WINDOW = 32

    def __init__(self):
        self.samples = []          # (rtt_s, offset_s)

    def update(self, t0, t1, t2, t3):
        rtt = (t3 - t0) - (t2 - t1)
        offset = ((t1 - t0) + (t2 - t3)) / 2.0
        self.samples.append((rtt, offset))
        del self.samples[:-self.WINDOW]

    def best(self):
        """(offset_s, rtt_s) of the min-rtt sample, or (None, None)."""
        if not self.samples:
            return (None, None)
        rtt, offset = min(self.samples)
        return (offset, rtt)
