# Architecture

```
 user text (en/hi/mr)
        │
        ▼
 ┌──────────────┐  mask scheme names   ┌───────────────────────────┐
 │ dialogue.py  │─────────────────────▶│ nlu.py                    │
 │ (session,    │◀── profile, needs,   │  detect_language          │
 │  intent,     │    intents           │  extract_profile/needs    │
 │  follow-up)  │                      │  parse_pending (yes/no/#) │
 └──────┬───────┘                      └───────────────────────────┘
        │ profile + needs
        ▼
 ┌──────────────┐   rank by status +   ┌───────────────────────────┐
 │ schemes.py   │   need-tag overlap   │ data/schemes.json         │
 │ (catalogue)  │◀────────────────────▶│ rules · docs · channels   │
 └──────┬───────┘                      └───────────────────────────┘
        │ rule tree + profile
        ▼
 ┌──────────────┐  Result tree (true/false/unknown per node)
 │ rules.py     │──────────────┐
 └──────────────┘              ▼
                        ┌──────────────┐     ┌──────────┐
                        │ explain.py   │────▶│ i18n.py  │ → reply in user's language
                        └──────────────┘     └──────────┘
```

## Design decisions
* **Eligibility is deterministic.** Rules are data (JSON trees) evaluated by `rules.py`; no model decides eligibility,
  so outcomes are auditable and explainable.
* **Three-valued logic.** Missing information => UNKNOWN (not "no"). `missing_attrs()` returns only attributes that can
  still change the outcome, so the assistant never asks irrelevant questions.
* **Next-question selection.** The attribute missing in the largest number of still-possible schemes is asked first
  (ties broken by a fixed priority list). Each attribute is asked at most once; the user can say "skip".
* **Transparency.** Each scheme card lists conditions with ✅/❌/❓ and the user's own value; ineligible results show
  only the failing conditions as reasons.
* **Multilingual by construction.** Text lives in `i18n.py` / scheme JSON; condition sentences are generated from
  templates, so adding a rule needs no new translations beyond the scheme name/summary.
* **Safe NLU.** Negation ("no bank account"), desire ("I want an LPG connection" => doesn't have one), child-vs-own
  age, scheme-name masking, Devanagari digits and NFC normalisation are handled explicitly and unit-tested.
* **LLM is optional and sandboxed**: extraction only, strict schema validation, rule-based fallback.
