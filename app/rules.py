"""Rule-based eligibility engine with three-valued (true / false / unknown) logic.

A rule is a JSON tree:
  {"all": [rule, ...]}  {"any": [rule, ...]}  {"not": rule}
  {"attr": "age", "op": "between", "value": [18, 40]}      <- leaf condition
Missing profile data yields UNKNOWN rather than a wrong yes/no, which is what lets the
assistant ask the right follow-up question instead of guessing.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

TRUE, FALSE, UNKNOWN = "true", "false", "unknown"
KNOWN_OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "between"}


@dataclass
class Result:
    status: str
    node: dict
    children: List["Result"] = field(default_factory=list)
    actual: Any = None


def _n(v):
    return v.lower() if isinstance(v, str) else v


def _compare(op, actual, expected):
    a = _n(actual)
    if op == "eq":
        return a == _n(expected)
    if op == "ne":
        return a != _n(expected)
    if op == "in":
        return a in [_n(x) for x in expected]
    if op == "not_in":
        return a not in [_n(x) for x in expected]
    if op == "between":
        return expected[0] <= a <= expected[1]
    if op == "gt":
        return a > expected
    if op == "gte":
        return a >= expected
    if op == "lt":
        return a < expected
    if op == "lte":
        return a <= expected
    raise ValueError(f"unknown op {op}")


def evaluate(node: dict, profile: Dict[str, Any]) -> Result:
    if "all" in node:
        kids = [evaluate(c, profile) for c in node["all"]]
        if any(k.status == FALSE for k in kids):
            st = FALSE
        elif all(k.status == TRUE for k in kids):
            st = TRUE
        else:
            st = UNKNOWN
        return Result(st, node, kids)
    if "any" in node:
        kids = [evaluate(c, profile) for c in node["any"]]
        if any(k.status == TRUE for k in kids):
            st = TRUE
        elif all(k.status == FALSE for k in kids):
            st = FALSE
        else:
            st = UNKNOWN
        return Result(st, node, kids)
    if "not" in node:
        kid = evaluate(node["not"], profile)
        st = {TRUE: FALSE, FALSE: TRUE, UNKNOWN: UNKNOWN}[kid.status]
        return Result(st, node, [kid])
    attr = node["attr"]
    actual = profile.get(attr)
    if actual is None:
        return Result(UNKNOWN, node, [], None)
    try:
        ok = _compare(node["op"], actual, node["value"])
    except TypeError:
        return Result(UNKNOWN, node, [], actual)
    return Result(TRUE if ok else FALSE, node, [], actual)


def missing_attrs(res: Result) -> List[str]:
    """Attributes whose answer could still change the outcome (ordered, de-duplicated)."""
    out: List[str] = []

    def walk(r: Result):
        n = r.node
        if "attr" in n:
            if r.status == UNKNOWN and n["attr"] not in out:
                out.append(n["attr"])
        elif "all" in n:
            if r.status != FALSE:
                for c in r.children:
                    walk(c)
        elif "any" in n:
            if r.status != TRUE:
                for c in r.children:
                    if c.status == UNKNOWN:
                        walk(c)
        elif "not" in n:
            walk(r.children[0])

    walk(res)
    return out


def validate(node: dict, known_attrs: Set[str]) -> List[str]:
    """Return a list of schema problems (empty = OK). Used by tests / data reviews."""
    errs: List[str] = []
    if "all" in node or "any" in node:
        for c in node.get("all", node.get("any")):
            errs += validate(c, known_attrs)
    elif "not" in node:
        errs += validate(node["not"], known_attrs)
    else:
        if node.get("attr") not in known_attrs:
            errs.append(f"unknown attr {node.get('attr')}")
        if node.get("op") not in KNOWN_OPS:
            errs.append(f"unknown op {node.get('op')}")
        if "value" not in node:
            errs.append("missing value")
    return errs
