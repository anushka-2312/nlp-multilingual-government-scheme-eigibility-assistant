# Scheme Mitra — Multilingual Government-Scheme Assistant (prototype)

A conversational assistant that:
1. **Understands** a citizen's free-text description (English / हिन्दी / मराठी) → structured profile + needs
2. **Identifies** relevant government schemes (need-based retrieval)
3. **Evaluates** rule-based eligibility with *three-valued logic* (eligible / not eligible / need more info)
4. **Explains** every decision condition-by-condition (✅ / ❌ / ❓, with the user's own values)
5. Gives **required documents** and **step-by-step application guidance**
6. Asks the **single most useful follow-up question** when information is missing

Pure Python 3.9+ standard library. No internet, no API key, no model download needed.

## Run it
```bash
python run_cli.py            # terminal chat
python run_web.py 8000       # web chat UI  -> http://localhost:8000
python -m unittest discover -s tests -t .    # 24 tests
```
Try: `I am a 45 year old farmer from Pune with 2 acres, family income 1.5 lakh` →
`documents for PM-KISAN` → `how to apply for sukanya` → `मैं 65 साल का हूँ, बीपीएल परिवार से, पेंशन चाहिए`

### HTTP API
| Endpoint | Body | Returns |
|---|---|---|
| `POST /api/chat` | `{"session_id","message"}` | reply, detected language, parsed profile, per-scheme status + explanation |
| `POST /api/evaluate` | `{"profile":{...},"lang":"hi"}` | stateless eligibility for all schemes |
| `GET /api/schemes` | – | catalogue |

## Project layout
```
app/nlu.py        language detection, profile/need/intent extraction (en/hi/mr, Devanagari digits, negation)
app/rules.py      eligibility engine (all/any/not trees, 3-valued logic, missing-attribute analysis)
app/schemes.py    catalogue loader, scheme-name detection, need-based ranking
app/explain.py    localised condition-by-condition explanations
app/dialogue.py   conversation state machine + follow-up question selection
app/i18n.py       every user-facing string in 3 languages
app/llm_nlu.py    OPTIONAL LLM extractor (validated, extraction only; off by default)
data/schemes.json 15 schemes: rules, documents, channels, portals, translations
docs/ARCHITECTURE.md
```

## Adding / editing a scheme (no code changes)
Add an object to `data/schemes.json -> schemes`:
```json
{"id":"my_scheme","aliases":["my scheme","माझी योजना"],
 "name":{"en":"…","hi":"…","mr":"…"}, "summary":{"en":"…","hi":"…","mr":"…"},
 "level":"central","state":null,"tags":["pension"],
 "eligibility":{"all":[{"attr":"age","op":"gte","value":60},
                       {"any":[{"attr":"is_bpl","op":"eq","value":true},
                               {"attr":"annual_income","op":"lte","value":100000}]}]},
 "documents":["aadhaar","bank_passbook"],
 "apply":{"portal":"https://…","offline":["csc"]}}
```
Operators: `eq ne gt gte lt lte in not_in between`. Attributes: `age gender state area annual_income occupation
category is_bpl owns_land has_pucca_house has_bank_account is_income_tax_payer has_lpg has_girl_child_under_10`.
`tests/test_dialogue.py::CatalogDataTest` validates new entries (known attrs/ops, all 3 languages, valid document ids).
To add a **new attribute**: add its label/question to `app/i18n.py` and an extractor in `app/nlu.py`.
To add a **language**: add its code to every dict in `i18n.py` and the scheme JSON, plus markers in `nlu.detect_language`.

## IMPORTANT — data & limitations
* **Scheme data is sample data for a prototype.** Rules are *simplified* (e.g. PM-JAY uses a BPL proxy for SECC
  criteria; PMAY income caps are approximations; amounts change). Verify every scheme against its official
  guidelines/portal and set up a review process before any real-world use.
* Income is treated as *household yearly income*; "monthly" amounts are multiplied by 12.
* The NLU is rule-based: robust for common phrasing, weaker on slang, Roman-script Hindi ("Hinglish"), spelling
  mistakes and complex sentences. `app/llm_nlu.py` shows how to plug in an LLM for extraction while keeping
  eligibility decisions deterministic (untested here — needs an API key).
* No personal data is stored beyond in-memory sessions. Do not collect Aadhaar numbers etc.

## Roadmap ideas
Voice input/output (Web Speech API, Bhashini), WhatsApp/IVR channel, more states & schemes, document-checklist
upload, retrieval over official PDFs for citations, "near me" CSC/office lookup, admin UI for rule authoring.
