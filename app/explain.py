"""Turn evaluation results into transparent, localised explanations."""
from typing import List, Optional, Set

from .i18n import attr_label, fmt_value, op_text, t
from .rules import FALSE, TRUE, UNKNOWN, Result

ICON = {TRUE: "✅", FALSE: "❌", UNKNOWN: "❓"}


def leaf_text(res: Result, lang: str) -> str:
    n = res.node
    attr, op, v = n["attr"], n["op"], n["value"]
    label = attr_label(attr, lang)
    if op == "between":
        txt = op_text(op, lang, label=label, lo=fmt_value(attr, v[0], lang), hi=fmt_value(attr, v[1], lang))
    elif op == "eq" and isinstance(v, bool):
        txt = t("req_bool", lang, label=label, v=fmt_value(attr, v, lang))
    elif op in ("in", "not_in"):
        txt = op_text(op, lang, label=label, v=", ".join(fmt_value(attr, x, lang) for x in v))
    else:
        txt = op_text(op, lang, label=label, v=fmt_value(attr, v, lang))
    if res.actual is None:
        return txt + t("unk", lang)
    return txt + t("you", lang, v=fmt_value(attr, res.actual, lang))


def render(res: Result, lang: str, depth: int = 0, only: Optional[Set[str]] = None) -> List[str]:
    """Readable bullet lines. `only` restricts leaves to given statuses (e.g. just the failing ones)."""
    ind = "   " * depth
    n = res.node
    if "attr" in n:
        if only and res.status not in only:
            return []
        return [f"{ind}{ICON[res.status]} {leaf_text(res, lang)}"]
    if "all" in n:
        out: List[str] = []
        for c in res.children:
            out += render(c, lang, depth, only)
        return out
    if "any" in n:
        if only and res.status not in only:
            return []
        out = [f"{ind}{ICON[res.status]} {t('any_of', lang)}"]
        for c in res.children:
            out += render(c, lang, depth + 1, None)
        return out
    return render(res.children[0], lang, depth, only)  # "not": show inner condition
