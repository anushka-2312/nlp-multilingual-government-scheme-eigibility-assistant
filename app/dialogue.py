"""Conversation manager: ties NLU -> retrieval -> rule engine -> explanation -> follow-up question."""
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from . import explain
from .i18n import attr_label, fmt_value, question, t
from .nlu import (detect_intents, detect_language, extract_needs, extract_profile, normalize, parse_pending)
from .rules import FALSE, TRUE, UNKNOWN
from .llm_nlu import extract_with_llm
from .schemes import Catalog

ASK_ORDER = ["age", "gender", "state", "occupation", "annual_income", "category", "area", "is_bpl", "owns_land",
             "has_pucca_house", "has_bank_account", "is_income_tax_payer", "has_lpg", "has_girl_child_under_10"]
RESET = {"reset", "restart", "start over", "new", "नया", "रीसेट", "पुन्हा सुरू", "रिसेट"}
SKIP = {"skip", "show results", "results", "done", "enough", "बस", "पुरे", "रहने दो"}
SHOW_ALL = re.compile(r"show all|सभी दिखा|सर्व दाखवा")
LANG_REQ = [(re.compile(r"\b(?:in|reply in|speak in)\s+hindi\b|हिंदी में|हिन्दी में"), "hi"),
            (re.compile(r"\b(?:in|reply in|speak in)\s+marathi\b|मराठीत|मराठी मध्ये"), "mr"),
            (re.compile(r"\b(?:in|reply in|speak in)\s+english\b"), "en")]
MAX_ELIGIBLE, MAX_POSSIBLE, MAX_NOT = 5, 4, 3


@dataclass
class Session:
    lang: Optional[str] = None
    lang_locked: bool = False
    profile: Dict[str, Any] = field(default_factory=dict)
    needs: Set[str] = field(default_factory=set)
    pending: Optional[str] = None
    asked: Set[str] = field(default_factory=set)
    focus: Optional[str] = None
    show_all: bool = False
    stop_asking: bool = False
    turns: int = 0


class Assistant:
    def __init__(self, catalog: Optional[Catalog] = None):
        self.catalog = catalog or Catalog()

    # ------------------------------------------------------------------ language
    def _pick_lang(self, s: Session, text: str) -> str:
        low = normalize(text).lower()
        for pat, code in LANG_REQ:
            if pat.search(low):
                s.lang, s.lang_locked = code, True
                return code
        if any("\u0900" <= ch <= "\u097f" for ch in text):
            s.lang = detect_language(text, default=s.lang or "hi")
        elif s.lang and (s.lang_locked or len(text.split()) <= 4):
            pass
        else:
            s.lang = "en"
        return s.lang

    # ------------------------------------------------------------------ main entry
    def handle(self, s: Session, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        s.turns += 1
        lang = self._pick_lang(s, text)
        low = normalize(text).lower().strip(" .!")

        if low in RESET:
            s.__dict__.update(Session(lang=lang, lang_locked=s.lang_locked).__dict__)
            return self._out(s, t("reset", lang) + "\n\n" + t("welcome", lang))

        clean = self.catalog.mask(text)
        updates = {**extract_with_llm(clean), **extract_profile(clean)}
        if s.pending and s.pending not in updates:
            v = parse_pending(s.pending, text)
            if v is not None:
                updates[s.pending] = v
        s.profile.update(updates)
        if s.pending:
            s.asked.add(s.pending)
            s.pending = None
        s.needs |= extract_needs(clean)
        if low in SKIP:
            s.stop_asking = True
        if SHOW_ALL.search(low):
            s.show_all = True

        mentions = self.catalog.mentions(text)
        intents = detect_intents(text)
        parts: List[str] = []
        if updates:
            parts.append(t("learned", lang, items="; ".join(
                f"{attr_label(a, lang)}: {fmt_value(a, v, lang)}" for a, v in updates.items())))

        results: List[Dict[str, Any]] = []
        asked_from: List[dict] = []

        if mentions or (intents & {"documents", "apply"} and s.focus):
            targets = mentions[:2] or [self.catalog.get(s.focus)]
            s.focus = targets[0]["id"]
            for sch in targets:
                e = self.catalog.evaluate(sch, s.profile)
                asked_from.append(e)
                results.append(self._summary(e, lang))
                if "documents" in intents:
                    parts.append(self._docs(sch, lang))
                if "apply" in intents:
                    if "documents" not in intents:
                        parts.append(self._docs(sch, lang))
                    parts.append(self._apply(sch, lang))
                if not (intents & {"documents", "apply"}) or "why" in intents:
                    parts.append(self._card(e, lang, full=True))
        elif intents & {"documents", "apply"}:
            parts.append(t("which_scheme", lang))
        elif not updates and not s.needs and not s.profile:
            return self._out(s, t("welcome", lang))
        else:
            ranked = self.catalog.rank(s.profile, s.needs)
            if s.needs:
                ranked = [e for e in ranked if e["need_score"] > 0]
            asked_from = ranked
            body, shown = self._ranking(ranked, lang, s)
            parts.append(body)
            results = [self._summary(e, lang) for e in shown]
            if len(shown) == 1:
                s.focus = shown[0]["scheme"]["id"]

        q = None
        if not s.stop_asking:
            q = self._next_question(s, asked_from)
        if q:
            s.pending = q
            parts.append("❓ " + question(q, lang) + "\n" + t("skip_hint", lang))
        parts.append(t("disclaimer", lang))
        return self._out(s, "\n\n".join(p for p in parts if p), results)

    # ------------------------------------------------------------------ rendering
    def _name(self, sch, lang):
        return sch["name"].get(lang) or sch["name"]["en"]

    def _summary(self, e, lang):
        return {"id": e["scheme"]["id"], "name": self._name(e["scheme"], lang), "status": e["status"],
                "missing": e["missing"], "explanation": explain.render(e["result"], lang)}

    def _card(self, e, lang, full=False):
        sch, res, st = e["scheme"], e["result"], e["status"]
        head = f"{explain.ICON[st]} {self._name(sch, lang)}\n   {sch['summary'].get(lang) or sch['summary']['en']}"
        only = None if full or st == TRUE else ({UNKNOWN} if st == UNKNOWN else {FALSE})
        lines = explain.render(res, lang, 1, only)
        if st == UNKNOWN and e["missing"]:
            lines.append("   " + t("still_needed", lang, items=", ".join(attr_label(a, lang) for a in e["missing"])))
        return head + ("\n" + "\n".join(lines) if lines else "")

    def _ranking(self, ranked, lang, s):
        elig = [e for e in ranked if e["status"] == TRUE]
        poss = [e for e in ranked if e["status"] == UNKNOWN]
        nots = [e for e in ranked if e["status"] == FALSE]
        if not s.needs and s.profile:   # no stated need: avoid showing a wall of long-shot "maybe" schemes
            poss = [e for e in poss if len(e["missing"]) <= 2]
        shown, blocks = [], []
        if elig:
            blocks.append(t("eligible_h", lang) + "\n\n" + "\n\n".join(self._card(e, lang) for e in elig[:MAX_ELIGIBLE]))
            shown += elig[:MAX_ELIGIBLE]
        if poss:
            blocks.append(t("possible_h", lang) + "\n\n" + "\n\n".join(self._card(e, lang) for e in poss[:MAX_POSSIBLE]))
            shown += poss[:MAX_POSSIBLE]
        if nots and (s.needs or s.show_all):
            lim = len(nots) if s.show_all else MAX_NOT
            blocks.append(t("not_h", lang) + "\n\n" + "\n\n".join(self._card(e, lang) for e in nots[:lim]))
            shown += nots[:lim]
        hidden = len(ranked) - len(shown)
        if not blocks:
            blocks.append(t("no_match", lang))
        else:
            blocks.append(t("tip", lang))
        if hidden > 0 and not s.show_all:
            blocks.append(t("hidden", lang, n=hidden))
        return "\n\n".join(blocks), shown

    def _docs(self, sch, lang):
        lines = [t("docs_h", lang, name=self._name(sch, lang))]
        for d in sch["documents"]:
            doc = self.catalog.documents[d]
            lines.append("  • " + (doc.get(lang) or doc["en"]))
        return "\n".join(lines)

    def _apply(self, sch, lang):
        ap = sch["apply"]
        where = ", ".join((self.catalog.channels[c].get(lang) or self.catalog.channels[c]["en"]) for c in ap["offline"])
        steps = [t("step1", lang), t("step_online", lang, url=ap["portal"])]
        if where:
            steps.append(t("step_offline", lang, where=where))
        steps.append(t("step_track", lang))
        return t("apply_h", lang, name=self._name(sch, lang)) + "\n" + "\n".join(f"  {i}. {x}" for i, x in enumerate(steps, 1))

    # ------------------------------------------------------------------ follow-up question
    def _next_question(self, s: Session, entries) -> Optional[str]:
        score: Counter = Counter()
        for e in entries:
            if e["status"] == FALSE:
                continue
            for a in e["missing"]:
                if a not in s.asked and a not in s.profile and a in ASK_ORDER:
                    score[a] += 1
        if not score:
            return None
        return max(score, key=lambda a: (score[a], -ASK_ORDER.index(a)))

    def _out(self, s: Session, reply: str, results: Optional[list] = None) -> Dict[str, Any]:
        return {"reply": reply.strip(), "lang": s.lang or "en", "profile": dict(s.profile), "needs": sorted(s.needs),
                "pending": s.pending, "results": results or []}

    # ------------------------------------------------------------------ stateless API
    def evaluate_profile(self, profile: Dict[str, Any], lang: str = "en", needs: Optional[Set[str]] = None) -> List[dict]:
        ranked = self.catalog.rank(profile, needs or set())
        return [self._summary(e, lang) for e in ranked]
