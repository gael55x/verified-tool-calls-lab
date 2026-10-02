"""Built-in ticket service fixture and adapter for `python -m vtc.check`.

The service is test-only. It binds 127.0.0.1 on an ephemeral port, keeps tickets in
a SQLite file, takes its fault from --fault, records audit events in the same file,
and exposes POST /_test/settle. None of that belongs in a production API.

    POST /tickets   Idempotency-Key: <id>   {"title": "..."}   ->   201 or 200 {"id": n}

Profiles:
  broken   remembers replies in memory, only after a reply was sent, and otherwise
           ignores the key. A lost reply, a late first attempt, overlapping attempts
           or a restart each insert a second ticket.
  durable  stores the key under a UNIQUE constraint and checks it inside the same
           BEGIN IMMEDIATE transaction as the insert, so repeats replay the stored
           ticket, including after a restart. Same key, different payload: 422.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from vtc.check import SCENARIOS, Observation

REPO_ROOT = Path(__file__).resolve().parents[1]
READY_TIMEOUT = 10.0
HOLD_LIMIT = 20.0  # a held late_commit request proceeds after this even if never released
SETTLE_LIMIT = 10.0
MAX_BODY = 4096
EXPECTED_PAYLOAD = json.dumps({"title": "printer on fire"}, sort_keys=True)


def _connect(db):
    return sqlite3.connect(db, timeout=5.0, isolation_level=None)


def _log(conn, event):
    conn.execute("INSERT INTO audit (event) VALUES (?)", (event,))


def _write_broken(conn, key, payload):
    ticket = conn.execute("INSERT INTO tickets (op_key, payload) VALUES (?, ?)", (key, payload)).lastrowid
    return 201, {"id": ticket}


def _write_durable(conn, key, payload):
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT id, payload FROM tickets WHERE op_key = ?", (key,)).fetchone()
        if row is None:
            ticket = conn.execute("INSERT INTO tickets (op_key, payload) VALUES (?, ?)", (key, payload)).lastrowid
            result = 201, {"id": ticket}
        elif row[1] == payload:
            result = 200, {"id": row[0]}
        else:
            result = 422, {"error": "idempotency key reused with a different payload"}
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    return result


WRITERS = {"broken": _write_broken, "durable": _write_durable}
PROFILES = tuple(WRITERS)


class TicketServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, db, profile, fault):
        super().__init__(("127.0.0.1", 0), TicketHandler)
        self.db, self.profile, self.fault = db, profile, fault
        self.cond = threading.Condition()
        self.in_flight = 0
        self.requests = 0
        self.replies = {}  # broken profile only: in-memory replay cache
        self.release = threading.Event()
        self.barrier = threading.Barrier(2, timeout=5.0)

    def release_hold(self, conn, *events):
        with self.cond:
            if self.fault != "late_commit" or self.release.is_set():
                return
            self.release.set()
        for event in events:
            _log(conn, event)


class TicketHandler(BaseHTTPRequestHandler):
    timeout = 10  # seconds; bounds reads on idle or stalled connections

    def log_message(self, format, *args):  # keep request lines out of CI logs
        pass

    def do_POST(self):
        if self.path == "/_test/settle":
            self._settle()
        elif self.path == "/tickets":
            server = self.server
            with server.cond:
                server.in_flight += 1
                server.requests += 1
                number = server.requests
            try:
                self._create(number)
            finally:
                with server.cond:
                    server.in_flight -= 1
                    server.cond.notify_all()
        else:
            self._reply(404, {"error": "not found"})

    def _create(self, number):
        server = self.server
        key = self.headers.get("Idempotency-Key", "")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            title = json.loads(self.rfile.read(length))["title"] if 0 < length <= MAX_BODY else None
        except (ValueError, KeyError, TypeError):
            title = None
        if not key or len(key) > 200 or not isinstance(title, str):
            self._reply(400, {"error": "send an Idempotency-Key header and a JSON body with a string title"})
            return
        payload = json.dumps({"title": title}, sort_keys=True)
        with server.cond:
            cached = server.replies.get(key)
        if cached is not None:  # only the broken profile fills this cache
            self._reply(200, cached)
            return
        conn = _connect(server.db)
        try:
            _log(conn, "request:received")
            self._fault_gate(conn, number)
            status, body = WRITERS[server.profile](conn, key, payload)
            _log(conn, {201: "effect:committed", 200: "effect:replayed", 422: "effect:payload_conflict"}[status])
            if number > 1:
                server.release_hold(conn, "late_commit:released")
            if server.fault == "lost_reply" and number == 1:
                _log(conn, "lost_reply:dropped_after_commit")
                self.close_connection = True  # the commit stands; the client never hears about it
                return
        finally:
            conn.close()
        if self._reply(status, body) and server.profile == "broken" and status == 201:
            with server.cond:
                server.replies[key] = body  # remembered only after the reply went out

    def _fault_gate(self, conn, number):
        server = self.server
        if server.fault == "late_commit" and number == 1:
            _log(conn, "late_commit:held")
            if not server.release.wait(HOLD_LIMIT):
                server.release_hold(conn, "late_commit:hold_timeout")
        elif server.fault == "concurrent" and number <= 2:
            try:
                if server.barrier.wait() == 0:
                    _log(conn, "concurrent:overlap")
            except threading.BrokenBarrierError:
                _log(conn, "concurrent:barrier_timeout")

    def _settle(self):
        server = self.server
        conn = _connect(server.db)
        try:
            server.release_hold(conn, "late_commit:released", "late_commit:released_at_settle")
        finally:
            conn.close()
        with server.cond:
            quiet = server.cond.wait_for(lambda: server.in_flight == 0, SETTLE_LIMIT)
        self._reply(200, {"quiesced": quiet})

    def _reply(self, status, body):
        data = json.dumps(body).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return True
        except OSError:  # the client already gave up on this request
            return False


def serve(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m vtc.http_example", description="Test-only ticket service for vtc.check; binds 127.0.0.1."
    )
    parser.add_argument("--db", required=True, help="SQLite file, kept across restarts")
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--fault", choices=[s.name for s in SCENARIOS], default="clean")
    args = parser.parse_args(argv)
    conn = _connect(args.db)
    try:
        unique = "UNIQUE" if args.profile == "durable" else ""
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, op_key TEXT NOT NULL {unique}, payload TEXT NOT NULL)"
        )
        conn.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, event TEXT NOT NULL)")
        if conn.execute("SELECT 1 FROM audit WHERE event = 'server:start'").fetchone():
            _log(conn, "restart:new_process")
        _log(conn, "server:start")
    finally:
        conn.close()
    server = TicketServer(args.db, args.profile, args.fault)
    print(f"READY {server.server_address[1]}", flush=True)
    server.serve_forever()


def _child_env():
    """Minimal environment for the server: no inherited tokens, keys or proxies."""
    env = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    if "SYSTEMROOT" in os.environ:  # Windows cannot open sockets without it
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


def default_client():
    """Load create_ticket from examples/ticket_client.py, wherever the caller runs from."""
    spec = importlib.util.spec_from_file_location("vtc_example_ticket_client", REPO_ROOT / "examples" / "ticket_client.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_ticket


class FixtureAdapter:
    """One fixture server process over one SQLite file; the vtc.check adapter contract."""

    def __init__(self, profile, client, db):
        self.profile, self.client, self.db = profile, client, db
        self.proc = None
        self.base_url = ""

    def start(self, fault):
        proc = self.proc = subprocess.Popen(
            [sys.executable, "-m", "vtc.http_example", "--db", str(self.db), "--profile", self.profile, "--fault", fault],
            cwd=REPO_ROOT,
            env=_child_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines = []
        reader = threading.Thread(target=lambda: lines.append(proc.stdout.readline()), daemon=True)
        reader.start()
        reader.join(READY_TIMEOUT)
        if not lines or not lines[0].startswith("READY "):
            raise RuntimeError("fixture server did not become ready")
        self.base_url = "http://127.0.0.1:" + str(int(lines[0].split()[1]))

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is not None:
            proc.kill()  # SIGKILL on POSIX: a crash, not a graceful shutdown
            proc.wait(timeout=10)
            proc.stdout.close()

    def invoke(self, operation_id):
        return self.client(self.base_url, operation_id)

    def restart(self):
        self.stop()
        self.start("clean")  # the new process runs without a fault

    def settle(self):
        request = urllib.request.Request(self.base_url + "/_test/settle", data=b"", method="POST")
        with urllib.request.urlopen(request, timeout=SETTLE_LIMIT + 5) as response:
            return json.load(response)["quiesced"] is True

    def observe(self, operation_id):
        # Counts every ticket in this isolated database, so a client that changes its
        # key between attempts shows up as a duplicate too.
        conn = sqlite3.connect(self.db.as_uri() + "?mode=ro", uri=True)
        try:
            effects = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            completed = conn.execute(
                "SELECT 1 FROM tickets WHERE op_key = ? AND payload = ?",
                (operation_id, EXPECTED_PAYLOAD),
            ).fetchone() is not None
            events = tuple(row[0] for row in conn.execute("SELECT event FROM audit ORDER BY id"))
        finally:
            conn.close()
        return Observation(completed=completed, effects=effects, events=events)


def fixture_factory(profile="durable", client=None):
    """Adapter factory for the built-in fixture; client(base_url, operation_id) -> bool."""
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of {PROFILES}")
    client = client or default_client()

    @contextlib.contextmanager
    def factory(scenario):
        with tempfile.TemporaryDirectory(prefix="vtc-retry-check-") as tmp:
            adapter = FixtureAdapter(profile, client, Path(tmp) / "tickets.sqlite3")
            try:
                adapter.start(scenario.name)
                yield adapter
            finally:
                adapter.stop()

    return factory


if __name__ == "__main__":
    serve()
