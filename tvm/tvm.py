#!/usr/bin/env python3
"""
tvm.py - Temporal Virtual Machine for Flux bytecode
"""

import sys
import json
import random
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------------------------------------------------
# Runtime values
# ----------------------------------------------------------------------

class Duration:
    def __init__(self, nanos: int, original: str = ""):
        self.nanos = nanos
        self.original = original or self._format(nanos)
    @staticmethod
    def _format(nanos):
        if nanos % 1_000_000_000 == 0:
            return f"{nanos // 1_000_000_000}s"
        if nanos % 1_000_000 == 0:
            return f"{nanos // 1_000_000}ms"
        if nanos % 1_000 == 0:
            return f"{nanos // 1_000}us"
        return f"{nanos}ns"
    def __repr__(self):
        return self.original
    def __add__(self, other):
        return Duration(self.nanos + other.nanos)
    def __sub__(self, other):
        return Duration(self.nanos - other.nanos)
    def __eq__(self, other):
        return isinstance(other, Duration) and self.nanos == other.nanos
    def __lt__(self, other):
        return self.nanos < other.nanos
    def __le__(self, other):
        return self.nanos <= other.nanos
    def __hash__(self):
        return hash(("Duration", self.nanos))

class Nil:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "nil"
    def __bool__(self):
        return False

NIL = Nil()

class Distribution:
    def __init__(self, entries: List[Tuple[Any, float]]):
        self.entries = [(v, w) for v, w in entries if w > 0]
        if not self.entries:
            self.entries = [(NIL, 1.0)]
    def __repr__(self):
        return "dist{" + ", ".join(f"{v}:{w}" for v, w in self.entries) + "}"

# ----------------------------------------------------------------------
# Hardware stub
# ----------------------------------------------------------------------

class _Hardware:
    def devices(self):
        return ["display", "keyboard", "uart", "gpio"]
    def read(self, dev, reg):
        return 0xDEADBEEF
    def write(self, dev, reg, val):
        pass

# ----------------------------------------------------------------------
# VM core
# ----------------------------------------------------------------------

class FluxRuntimeError(Exception):
    pass

class TemporalVM:
    def __init__(self, input_provider=None, sink=None, rng_seed=None):
        self.input_provider = input_provider or InputProvider()
        self.sink = sink or OutputSink()
        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        self.clock_ns = 0
        self.step = 0
        self.current_timeline = "primary"
        self.timeline_counter = 1
        self.known_timelines = {"primary"}
        self.mosaics: Dict[str, Dict[Any, List[Tuple[Any, float]]]] = {}
        self.intentions = []
        self.functions = {}
        self.flows = {}
        self.hardware = _Hardware()

    def load_module(self, filename: str):
        with open(filename, 'r') as f:
            data = json.load(f)
        self.intentions = []
        for i in data.get("intentions", []):
            # In a real VM we'd reconstruct CodeObject, but for simplicity we store as dict
            self.intentions.append(i)
        for f in data.get("functions", []):
            self.functions[f["name"]] = f
        for f in data.get("flows", []):
            self.flows[f["name"]] = f
        for m in data.get("mosaics", []):
            self.mosaics.setdefault(m["name"], {})

    def run_module(self):
        # sort intentions by priority (highest first)
        sorted_intent = sorted(self.intentions, key=lambda i: -i.get("priority", 1.0))
        for intent in sorted_intent:
            self.run_intention(intent)

    def run_intention(self, intent):
        # Evaluate trigger and condition (simplified: always true if not present)
        # In a full VM we would compile and evaluate the AST, but here we simulate.
        # For the purpose of the demo, we just execute the bytecode.
        self.execute_bytecode(intent["instructions"])

    def execute_bytecode(self, instrs):
        stack = []
        ip = 0
        while ip < len(instrs):
            op_name, arg = instrs[ip]
            ip += 1
            if op_name == "PUSH_NUM":
                stack.append(float(arg))
            elif op_name == "PUSH_STR":
                stack.append(arg)
            elif op_name == "PUSH_BOOL":
                stack.append(bool(arg))
            elif op_name == "PUSH_DURATION":
                nanos, orig = arg
                stack.append(Duration(nanos, orig))
            elif op_name == "PUSH_NIL":
                stack.append(NIL)
            elif op_name == "POP":
                stack.pop()
            elif op_name == "BIN_OP":
                b = stack.pop()
                a = stack.pop()
                stack.append(self.binop(a, arg, b))
            elif op_name == "UNARY_OP":
                v = stack.pop()
                stack.append(self.unaryop(arg, v))
            elif op_name == "CALL":
                name, argc = arg
                args = [stack.pop() for _ in range(argc)][::-1]
                res = self.call(name, args)
                stack.append(res)
            elif op_name == "METHOD_CALL":
                method, argc = arg
                args = [stack.pop() for _ in range(argc)][::-1]
                receiver = stack.pop()
                res = self.method_call(receiver, method, args)
                stack.append(res)
            elif op_name == "FIELD_ACCESS":
                receiver = stack.pop()
                stack.append(self.field_access(receiver, arg))
            elif op_name == "SEND_SENSATION":
                dur = stack.pop()
                cont = stack.pop()
                kind = stack.pop()
                self.sink.emit(kind, cont, dur if isinstance(dur, Duration) else None)
            elif op_name == "LISTEN":
                source, has_timeout, has_fallback = arg
                fallback = stack.pop() if has_fallback else None
                timeout = stack.pop() if has_timeout else None
                stack.append(self.input_provider.listen(source, timeout, fallback))
            elif op_name == "COLLAPSE":
                method = arg
                v = stack.pop()
                stack.append(self.collapse(v, method))
            elif op_name == "LAUNCH":
                name, argc = arg
                args = [stack.pop() for _ in range(argc)][::-1]
                self.launch(name, args)
            elif op_name == "LOAD_VAR":
                # For demonstration, we treat vars as a simple dict
                # In a real VM we'd have scopes. Here we just push a placeholder.
                stack.append("variable_" + arg)
            elif op_name == "STORE_VAR":
                val = stack.pop()
                # ignore
            elif op_name == "DECLARE_VAR":
                val = stack.pop()
                # ignore
            elif op_name == "RETURN":
                return stack.pop() if stack else NIL
            else:
                raise FluxRuntimeError(f"Unhandled op {op_name}")
        return NIL

    def binop(self, a, op, b):
        if op == "++":
            return str(a) + str(b)
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        if op == "&&":
            return self.truthy(a) and self.truthy(b)
        if op == "||":
            return self.truthy(a) or self.truthy(b)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        if op == "%":
            return a % b
        raise FluxRuntimeError(f"Unknown binary op {op}")

    def unaryop(self, op, v):
        if op == "-":
            return -v
        if op == "!":
            return not self.truthy(v)
        raise FluxRuntimeError(f"Unknown unary op {op}")

    def truthy(self, v):
        if v is NIL:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, str):
            return len(v) > 0
        if isinstance(v, Duration):
            return v.nanos != 0
        if isinstance(v, (list, tuple, dict)):
            return len(v) > 0
        return True

    def call(self, name, args):
        # Built-in functions
        if name == "now":
            self.clock_ns += 100000000
            return Duration(self.clock_ns)
        if name == "to_string":
            return str(args[0]) if args else ""
        if name == "parse_duration":
            s = args[0] if args else "0s"
            # simplistic parser
            if s.endswith("s"):
                return Duration(int(float(s[:-1]) * 1_000_000_000))
            return Duration(0)
        if name == "current_timeline":
            return self.current_timeline
        if name == "create_timeline":
            self.timeline_counter += 1
            name = f"timeline_{self.timeline_counter}"
            self.known_timelines.add(name)
            return name
        if name == "set_current_timeline":
            if args and args[0] in self.known_timelines:
                self.current_timeline = args[0]
            return NIL
        if name == "merge_timelines":
            if args and args[0] in self.known_timelines:
                self.known_timelines.discard(args[0])
            return NIL
        if name == "list_timelines":
            return list(self.known_timelines)
        if name == "timeline_exists":
            return args[0] in self.known_timelines if args else False
        if name == "reset_timeline":
            # stub
            return NIL
        if name == "generate_paradox":
            # stub: return deterministic string
            return f"P{self.step:06d}"
        if name == "resolve_paradox":
            return args[0] if args else NIL
        if name == "save_mosaic":
            self._save_mosaic(args[0] if args else "state/mosaic.json")
            return NIL
        if name == "load_mosaic":
            self._load_mosaic(args[0] if args else "state/mosaic.json")
            return NIL
        if name == "sparse_temporal_matrix":
            return {"_kind": "sparse_temporal_matrix"}
        if name == "sleep":
            if args and isinstance(args[0], Duration):
                self.clock_ns += args[0].nanos
            return NIL
        if name == "send":
            # already handled via SEND_SENSATION, but direct call may occur
            return NIL
        if name == "listen":
            # direct call not used, but we can simulate
            return ""
        if name == "print":
            print(*[str(a) for a in args])
            return NIL
        if name == "support":
            if args and isinstance(args[0], Distribution):
                return [v for v, _ in args[0].entries]
            return []
        if name == "weight_of":
            if len(args) >= 2 and isinstance(args[0], Distribution):
                target = args[1]
                return sum(w for v, w in args[0].entries if v == target)
            return 0.0
        if name == "normalize":
            if args and isinstance(args[0], Distribution):
                d = args[0]
                total = sum(w for _, w in d.entries)
                if total <= 0:
                    return Distribution(d.entries)
                return Distribution([(v, w/total) for v, w in d.entries])
            return Distribution([])
        if name == "to_lower":
            return args[0].lower() if args and isinstance(args[0], str) else ""
        if name == "contains":
            return args[0] in args[1] if len(args) >= 2 else False
        if name == "join":
            delim = args[1] if len(args) >= 2 else ""
            return delim.join([str(x) for x in args[0]]) if args else ""
        if name == "random_int":
            minv = int(args[0]) if args else 0
            maxv = int(args[1]) if len(args) >= 2 else 100
            return self.rng.randint(minv, maxv)
        if name == "clamp":
            x = args[0] if args else 0
            return max(0, min(1, x))
        if name == "hardware":
            return self.hardware
        # User function (stub)
        return NIL

    def method_call(self, receiver, method, args):
        if method == "write":
            # mosaic cursor method
            # In a full implementation, we'd handle mosaic.accept(key).write(value, weight)
            return NIL
        if method == "read":
            return NIL
        if method == "accept":
            return {"_cursor": receiver, "_key": args[0] if args else None}
        if method == "exists":
            if isinstance(receiver, _Hardware):
                return True
            return False
        if method == "to_string":
            return str(receiver)
        raise FluxRuntimeError(f"Unknown method {method}")

    def field_access(self, receiver, field):
        if isinstance(receiver, dict):
            return receiver.get(field, NIL)
        raise FluxRuntimeError(f"No field {field}")

    def collapse(self, value, method):
        # simplified collapse
        if isinstance(value, Distribution):
            entries = value.entries
        else:
            entries = [(value, 1.0)]
        if method == "max_weight":
            return max(entries, key=lambda e: e[1])[0]
        if method == "weighted_random" or method == "random":
            total = sum(w for _, w in entries)
            r = self.rng.random() * total
            acc = 0.0
            for v, w in entries:
                acc += w
                if r <= acc:
                    return v
            return entries[-1][0]
        return entries[0][0]

    def launch(self, name, args):
        # find intention or flow and execute its bytecode
        for i in self.intentions:
            if i["name"] == name:
                self.execute_bytecode(i["instructions"])
                return
        # if not found, ignore

    def _save_mosaic(self, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        data = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mosaics": {}
        }
        for mosaic_name, store in self.mosaics.items():
            data["mosaics"][mosaic_name] = {}
            for key, entries in store.items():
                data["mosaics"][mosaic_name][key] = [
                    {"value": self._serialize_value(v), "weight": w}
                    for v, w in entries
                ]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def _load_mosaic(self, filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        if "mosaics" not in data:
            return
        for mosaic_name, store_data in data["mosaics"].items():
            if mosaic_name not in self.mosaics:
                self.mosaics[mosaic_name] = {}
            for key, entries in store_data.items():
                self.mosaics[mosaic_name][key] = [
                    (self._deserialize_value(entry["value"]), entry["weight"])
                    for entry in entries
                ]

    def _serialize_value(self, v):
        if isinstance(v, Duration):
            return {"__type__": "Duration", "nanos": v.nanos, "original": v.original}
        if isinstance(v, Distribution):
            return {"__type__": "Distribution", "entries": [(self._serialize_value(val), w) for val, w in v.entries]}
        if isinstance(v, (list, tuple)):
            return [self._serialize_value(item) for item in v]
        if isinstance(v, dict):
            return {k: self._serialize_value(v) for k, v in v.items()}
        return v

    def _deserialize_value(self, obj):
        if isinstance(obj, dict) and "__type__" in obj:
            if obj["__type__"] == "Duration":
                return Duration(obj["nanos"], obj["original"])
            if obj["__type__"] == "Distribution":
                entries = [(self._deserialize_value(v), w) for v, w in obj["entries"]]
                return Distribution(entries)
        if isinstance(obj, list):
            return [self._deserialize_value(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self._deserialize_value(v) for k, v in obj.items()}
        return obj


class InputProvider:
    def __init__(self, scripted: Optional[Dict[str, List[str]]] = None):
        self.scripted = {k: list(v) for k, v in (scripted or {}).items()}
    def listen(self, source: str, timeout: Optional[Duration], fallback: Any) -> Any:
        queue = self.scripted.get(source)
        if queue:
            return queue.pop(0)
        # For user input, read from stdin if in REPL mode
        if source == "user":
            try:
                line = input("> ")
                return line
            except EOFError:
                return ""
        return fallback if fallback is not None else NIL

class OutputSink:
    def __init__(self, capture: bool = False):
        self.capture = capture
        self.events = []
    def emit(self, kind: str, content: Any, duration: Optional[Duration]):
        self.events.append((kind, content, duration))
        if not self.capture:
            dur = f" [{duration}]" if duration else ""
            print(f"[{kind}] {content}{dur}")

# ----------------------------------------------------------------------
# Main entry point (if run as script)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: tvm.py <bytecode.fluxb> [--repl]")
        sys.exit(1)
    filename = sys.argv[1]
    vm = TemporalVM(input_provider=InputProvider(), sink=OutputSink())
    vm.load_module(filename)
    # For a full system, we would run the scheduler loop.
    # Here we just run the module once.
    vm.run_module()