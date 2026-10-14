"""OPTIONAL: LLM-based profile extraction for messy / code-mixed input.

Enable with:  pip install anthropic ; export ANTHROPIC_API_KEY=... ; export USE_LLM_NLU=1
The LLM is used ONLY to extract facts (never to decide eligibility). Its output is validated against
a strict schema, and anything it cannot supply falls back to the rule-based extractor.
(This module is provided as an integration point and is not exercised by the offline tests.)
"""
import json
import os
from typing import Any, Dict

ENUMS = {"gender": {"male", "female"}, "area": {"rural", "urban"}, "category": {"general", "obc", "sc", "st"},
         "occupation": {"farmer", "student", "artisan", "business", "salaried", "govt_employee", "labourer",
                        "homemaker", "unemployed", "retired"}}
INTS = {"age": (0, 120), "annual_income": (0, 10**9)}
BOOLS = {"is_bpl", "owns_land", "has_pucca_house", "has_bank_account", "is_income_tax_payer", "has_lpg",
         "has_girl_child_under_10"}
PROMPT = ("Extract a citizen profile from the user's message (English/Hindi/Marathi). Reply with ONLY a JSON object. "
          "Allowed keys: age(int), gender(male|female), state(lowercase Indian state), area(rural|urban), "
          "annual_income(int rupees per YEAR for the household), occupation(" + "|".join(sorted(ENUMS['occupation'])) + "), "
          "category(general|obc|sc|st), " + ", ".join(sorted(BOOLS)) + "(booleans). "
          "Include a key ONLY if the user explicitly stated it. Never guess.")


def validate(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if k in ENUMS and isinstance(v, str) and v.lower() in ENUMS[k]:
            out[k] = v.lower()
        elif k in INTS and isinstance(v, (int, float)) and INTS[k][0] <= v <= INTS[k][1]:
            out[k] = int(v)
        elif k in BOOLS and isinstance(v, bool):
            out[k] = v
        elif k == "state" and isinstance(v, str):
            out[k] = v.lower().strip()
    return out


def extract_with_llm(text: str) -> Dict[str, Any]:
    if os.getenv("USE_LLM_NLU") != "1" or not os.getenv("ANTHROPIC_API_KEY"):
        return {}
    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), max_tokens=400,
                                     system=PROMPT, messages=[{"role": "user", "content": text}])
        raw = "".join(b.text for b in msg.content if getattr(b, "text", None))
        raw = raw[raw.find("{"): raw.rfind("}") + 1]
        return validate(json.loads(raw))
    except Exception:
        return {}
