"""Synthetic API with separate response, committed-effect and read-view channels.

All delays/failures are virtual logical events. No network, database, OS crashes,
LLM, threads or real side effects. Only evaluation code uses truth_snapshot().
"""
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import random

SUCCESS, FAILURE, AMBIGUOUS = "SUCCESS", "FAILURE", "AMBIGUOUS"
TRUE, FALSE, UNKNOWN = "TRUE", "FALSE", "UNKNOWN"
TASKS = ("activate_customer", "record_invoice")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Action:
    task: str
    payload: dict
    operation_id: str
    agent_id: str = "scripted-agent"
    timestamp_bucket: int = 0


@dataclass(frozen=True)
class Fault:
    effect: str = "full"  # full, partial (first 2 stages), none
    response: str = SUCCESS
    visibility_delay: int = 0
    unknown_until: int = 0
    commit_delay: int = 0


def fixture(task, seed):
    if task not in TASKS:
        raise ValueError(task)
    rng = random.Random(seed)
    return Action(task, {"customer_id": f"synthetic-c{seed}",
                         "invoice_id": f"synthetic-i{seed}",
                         "amount": rng.randrange(1, 10001)},
                  f"{task}-logical-{seed}")


LEVELS = {"low": (.05, .05, .03, .02),
          "medium": (.20, .15, .10, .05),
          "high": (.35, .25, .15, .10)}
PATTERNS = ("clean", "commit_timeout", "false_success", "partial_success",
            "no_effect_timeout", "stale_false", "delayed_unknown",
            "delayed_commit", "unknown_forever", "definitive_conflict",
            "partial_ambiguous", "commit_after_budget")


def main_tape(seed, level):
    """Four independent flags per potential attempt, fixed before dispatch."""
    rng = random.Random(seed)
    tape, flags = [], []
    for _ in range(2):
        timeout, delayed, partial, conflict = (
            rng.random() < p for p in LEVELS[level])
        flags.append(dict(timeout=timeout, delayed=delayed,
                          partial=partial, conflict=conflict))
        tape.append(Fault("none", FAILURE) if conflict else
                    Fault("partial" if partial else "full",
                          AMBIGUOUS if timeout or delayed else SUCCESS,
                          visibility_delay=2 if delayed else 0))
    return tape, flags


def stress_tape(pattern):
    first = {
        "clean": Fault(),
        "commit_timeout": Fault(response=AMBIGUOUS),
        "false_success": Fault("none", SUCCESS),
        "partial_success": Fault("partial", SUCCESS),
        "no_effect_timeout": Fault("none", AMBIGUOUS),
        "stale_false": Fault(response=AMBIGUOUS, visibility_delay=2),
        "delayed_unknown": Fault(response=AMBIGUOUS, visibility_delay=2,
                                 unknown_until=2),
        "delayed_commit": Fault(response=AMBIGUOUS, commit_delay=2),
        "unknown_forever": Fault("none", AMBIGUOUS, unknown_until=99),
        "definitive_conflict": Fault("none", FAILURE),
        "partial_ambiguous": Fault("partial", AMBIGUOUS),
        "commit_after_budget": Fault(response=AMBIGUOUS, commit_delay=5,
                                     unknown_until=5),
    }
    return [first[pattern], Fault()]


def paper_predicate(action, view):
    """Section 4.3 displayed formulas, with explicit ACTIVE normalization."""
    if action.task == "activate_customer":
        c = view.get("customer", {})
        return c.get("status") == "ACTIVE" and c.get("activated_at") is not None
    row = view.get("row", {})
    return (bool(row) and row.get("invoice_id") == action.payload["invoice_id"]
            and row.get("amount") == action.payload["amount"])


def task_predicate(action, view):
    """Narrative task success, independent of wrapper return status."""
    if not paper_predicate(action, view):
        return False
    if action.task == "activate_customer":
        return (view["customer"].get("id") == action.payload["customer_id"]
                and len(view.get("messages", [])) == 1
                and view["messages"][0]["customer_id"] == action.payload["customer_id"])
    return any(r.get("invoice_id") == action.payload["invoice_id"]
               and r.get("amount") == action.payload["amount"]
               and r.get("status") == "RECORDED" for r in view.get("records", []))


def duplicate_count(action, view):
    return max(0, len(view.get("messages" if action.task == "activate_customer"
                               else "records", [])) - 1)


def full_predicate(action, view):
    return task_predicate(action, view) and duplicate_count(action, view) == 0


class ToolPort:
    """Public capability surface. Wrappers have no truth/trace access.

    This is an interface discipline, not a Python sandbox/security boundary.
    Returned views are deep copies. Intentional introspection is out of scope.
    """
    __slots__ = ("__execute", "__response", "__read", "__wait", "__note")

    def __init__(self, env):
        self.__execute, self.__response = env.execute, env.get_response
        self.__read, self.__wait, self.__note = env.read, env.wait, env.note

    def execute(self, action, key=None):
        self.__execute(action, key)

    def response(self):
        return self.__response()

    def read(self, action):
        return self.__read(action)

    def wait(self, ticks):
        self.__wait(ticks)

    def note(self, kind, **values):
        self.__note(kind, **values)


class Environment:
    def __init__(self, tape, supported):
        if not tape:
            raise ValueError("empty fault tape")
        self.tape, self.supported = list(tape), supported
        self.tick, self.calls, self.reads, self.writes = 0, 0, 0, 0
        self.trace, self._truth, self._receipts = [], {}, {}
        self._pending, self._reserved = [], set()
        self._hidden_until, self._old_views, self._unknown_until = {}, {}, {}
        self._response = None

    def port(self):
        return ToolPort(self)

    def note(self, kind, **values):
        self.trace.append(dict(seq=len(self.trace), tick=self.tick, kind=kind, **values))

    def execute(self, action, key=None):
        if self.calls >= len(self.tape):
            raise RuntimeError("fault tape exhausted: wrapper exceeded call bound")
        f = self.tape[self.calls]
        self.calls += 1
        self.note("dispatch", attempt=self.calls, key=key,
                  action=asdict(action), fault=asdict(f))
        op = action.operation_id
        if f.visibility_delay:
            self._old_views[op] = deepcopy(self._truth.get(op, {}))
            self._hidden_until[op] = self.tick + f.visibility_delay
        if f.unknown_until:
            self._unknown_until[op] = max(self._unknown_until.get(op, 0),
                                          self.tick + f.unknown_until)
        effective_key = key if self.supported else None
        self._response = f.response
        if effective_key and effective_key in self._reserved:
            self.note("dedupe_pending", key=key)
        elif f.effect != "none":
            if f.commit_delay:
                if effective_key:
                    self._reserved.add(effective_key)
                self._pending.append((self.tick + f.commit_delay, action,
                                      effective_key, f.effect))
                self.note("schedule_commit", due=self.tick + f.commit_delay, key=key)
            else:
                self._apply(action, effective_key, f.effect)
        self.note("response_available", response=f.response)

    def get_response(self):
        self.note("response_inspected", response=self._response)
        return self._response

    def _apply(self, action, key, effect):
        view = self._truth.setdefault(action.operation_id, {})
        receipts = self._receipts.setdefault(key, set()) if key else set()
        for stage in range(2 if effect == "partial" else 3):
            if key and stage in receipts:
                self.note("dedupe_stage", stage=stage, key=key)
                continue
            p = action.payload
            if action.task == "activate_customer":
                if stage == 0:
                    view.setdefault("customer", {"id": p["customer_id"],
                                                  "status": "NEW", "activated_at": None})
                elif stage == 1:
                    view["customer"].update(status="ACTIVE", activated_at=self.tick)
                else:
                    view.setdefault("messages", []).append({"customer_id": p["customer_id"],
                                                             "message": "welcome"})
            elif action.task == "record_invoice":
                if stage == 0:
                    view["row"] = {"invoice_id": p["invoice_id"], "amount": p["amount"]}
                elif stage == 1:
                    view.setdefault("records", []).append({"invoice_id": p["invoice_id"],
                                                            "amount": p["amount"],
                                                            "status": "PENDING"})
                else:
                    view["records"][-1]["status"] = "RECORDED"
            else:
                raise ValueError(action.task)
            receipts.add(stage)
            self.writes += 1
            self.note("commit_stage", operation_id=action.operation_id,
                      stage=stage, key=key, state=deepcopy(view))

    def read(self, action):
        self.reads += 1
        op = action.operation_id
        if self.tick < self._unknown_until.get(op, 0):
            self.note("read", operation_id=op, outcome=UNKNOWN)
            return None
        stale = self.tick < self._hidden_until.get(op, 0)
        view = deepcopy(self._old_views.get(op, {}) if stale else self._truth.get(op, {}))
        self.note("read", operation_id=op, stale=stale, view=view)
        return view

    def wait(self, ticks):
        if not isinstance(ticks, int) or ticks < 0:
            raise ValueError("wait requires nonnegative integer virtual ticks")
        target = self.tick + ticks
        self.note("wait", ticks=ticks)
        due = sorted((x for x in self._pending if x[0] <= target), key=lambda x: x[0])
        self._pending = [x for x in self._pending if x[0] > target]
        for when, action, key, effect in due:
            self.tick = when
            self._apply(action, key, effect)
            self._reserved.discard(key)
        self.tick = target

    def truth_snapshot(self, action):
        """Evaluator only. Never passed to wrappers/verifiers."""
        return deepcopy(self._truth.get(action.operation_id, {}))

    def settle(self, horizon=8):
        if self.tick > horizon:
            raise AssertionError("wrapper exceeded observation horizon")
        self.wait(horizon - self.tick)
        if self._pending:
            raise AssertionError("unsettled committed effects at horizon")
