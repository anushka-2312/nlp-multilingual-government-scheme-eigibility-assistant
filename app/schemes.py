"""Scheme catalogue: loading, mention detection, matching and ranking."""
import json
import pathlib
from typing import Any, Dict, List, Optional, Set

from .nlu import find_terms, normalize
from .rules import FALSE, TRUE, UNKNOWN, Result, evaluate, missing_attrs

DATA_FILE = pathlib.Path(__file__).resolve().parent.parent / "data" / "schemes.json"
_ORDER = {TRUE: 0, UNKNOWN: 1, FALSE: 2}


class Catalog:
    def __init__(self, path: Optional[pathlib.Path] = None):
        raw = json.loads(pathlib.Path(path or DATA_FILE).read_text(encoding="utf-8"))
        self.documents: Dict[str, dict] = raw["documents"]
        self.channels: Dict[str, dict] = raw["channels"]
        self.schemes: List[dict] = raw["schemes"]
        self._by_id = {s["id"]: s for s in self.schemes}

    def get(self, scheme_id: str) -> Optional[dict]:
        return self._by_id.get(scheme_id)

    def mentions(self, text: str) -> List[dict]:
        tl = normalize(text).lower()
        hits = []
        for s in self.schemes:
            spans = find_terms(tl, s["aliases"])
            if spans:
                hits.append((spans[0][0], s))
        return [s for _, s in sorted(hits, key=lambda x: x[0])]

    def mask(self, text: str) -> str:
        """Blank out scheme names so e.g. 'PM-KISAN' is not read as 'I am a kisan (farmer)'."""
        t0 = normalize(text)
        tl = t0.lower()
        chars = list(t0)
        for s in self.schemes:
            for a, b in find_terms(tl, s["aliases"]):
                for i in range(a, min(b, len(chars))):
                    chars[i] = " "
        return "".join(chars)

    def evaluate(self, scheme: dict, profile: Dict[str, Any]) -> dict:
        res: Result = evaluate(scheme["eligibility"], profile)
        return {"scheme": scheme, "result": res, "status": res.status, "missing": missing_attrs(res)}

    def rank(self, profile: Dict[str, Any], needs: Set[str]) -> List[dict]:
        entries = []
        for s in self.schemes:
            e = self.evaluate(s, profile)
            e["need_score"] = len(set(s["tags"]) & needs)
            entries.append(e)
        entries.sort(key=lambda e: (_ORDER[e["status"]], -e["need_score"], e["scheme"]["name"]["en"]))
        return entries
