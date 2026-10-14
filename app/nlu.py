"""Offline, rule-based natural-language understanding for English / Hindi / Marathi.

Turns free text into
  * a citizen profile  (age, state, income, occupation, ...)      -> extract_profile()
  * the kinds of help they want (housing, health, loan, ...)      -> extract_needs()
  * what they are asking about a scheme (documents / apply / why) -> detect_intents()
Everything is deterministic and explainable. An optional LLM extractor (llm_nlu.py) can
be plugged in for messier input; this module remains the safe fallback.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set

from .i18n import nfc

_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).translate(_DIGITS)


# ----------------------------------------------------------------------------- helpers
def find_terms(text_l: str, terms: List[str]) -> List[tuple]:
    """Spans of any term. ASCII terms need word boundaries; Indic terms use substring match
    (Python's \\b is unreliable around Devanagari vowel signs)."""
    spans = []
    for term in terms:
        tl = nfc(term.lower())
        if tl.isascii():
            pat = r"(?<![a-z0-9])" + re.escape(tl) + r"(?:s|es)?(?![a-z0-9])"
        else:
            pat = re.escape(tl)
        spans += [m.span() for m in re.finditer(pat, text_l)]
    return sorted(spans)


_CLAUSE = re.compile(r"[,.;!?।]|\b(?:and|but|while|however|though)\b|(?<=\s)(?:और|आणि|पण|लेकिन|मगर)(?=\s)")
_NEG_BEFORE = re.compile(r"\b(?:no|not|never|without|don't|dont|do not|doesn't|does not|didn't|haven't|"
                         r"have not|hasn't|lack|lacking|cannot|can't)\b[\w\s']{0,15}$")
_NEG_AFTER = re.compile(r"^\W*(?:(?:is|are|was|am|have|has)\s+)?(?:not|no)\b|(?:नहीं|नही|नाही|नाहीये|नको)")
_DESIRE_BEFORE = re.compile(r"\b(?:want|wants|need|needs|apply|applying|looking|get|getting|require|interested|"
                            r"open|opening)\b[\w\s']{0,15}$")
_DESIRE_AFTER = re.compile(nfc(r"चाहिए|चाहिये|हवे|हवी|हवा|पाहिजे|पाहिजेत|खोलना|उघडायचे|काढायचे"))


def _before(tl, pos):
    return _CLAUSE.split(tl[:pos])[-1]


def _after(tl, pos, n=22):
    return _CLAUSE.split(tl[pos:pos + n])[0]


def _negated(tl, s, e):
    return bool(_NEG_BEFORE.search(_before(tl, s))) or bool(_NEG_AFTER.search(_after(tl, e)))


def _desired(tl, s, e):
    return bool(_DESIRE_BEFORE.search(_before(tl, s))) or bool(_DESIRE_AFTER.search(_after(tl, e)))


# ----------------------------------------------------------------------------- language
_MR = {"आहे", "आहेत", "मी", "मला", "माझे", "माझी", "माझा", "नाही", "आणि", "कसे", "कसा", "काय", "वर्षांचा",
       "वर्षांची", "शेतकरी", "अर्ज", "कागदपत्रे", "उत्पन्न", "वय", "पाहिजे", "हवी", "हवे", "करायचा", "राहतो",
       "राहते", "आहात", "आहोत", "तुम्ही", "तुमचे", "मिळेल"}
_HI = {"है", "हैं", "हूँ", "हूं", "मैं", "मेरा", "मेरी", "मेरे", "नहीं", "और", "कैसे", "क्या", "साल", "आय",
       "किसान", "आवेदन", "चाहिए", "करना", "रहता", "रहती", "आप", "आपका", "आपकी", "दस्तावेज़", "दस्तावेज"}


def detect_language(text: str, default: str = "en") -> str:
    dev = sum(1 for c in text if "\u0900" <= c <= "\u097f")
    letters = sum(1 for c in text if c.isalpha())
    if not letters or dev / letters < 0.3:
        return "en" if letters else default
    toks = [w.strip(".,!?;:।\"'()") for w in nfc(text).split()]
    mr = sum(1 for w in toks if w in _MR)
    hi = sum(1 for w in toks if w in _HI)
    if mr > hi:
        return "mr"
    if hi > mr:
        return "hi"
    return default if default in ("hi", "mr") else "hi"


# ----------------------------------------------------------------------------- money & age
_UNIT = {"lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5, "thousand": 1e3, "k": 1e3, "crore": 1e7,
         "crores": 1e7, nfc("लाख"): 1e5, nfc("हजार"): 1e3, nfc("हज़ार"): 1e3, nfc("करोड़"): 1e7, nfc("करोड"): 1e7}
_AMT = (r"(?:₹|rs\.?|inr|रु\.?|रुपये|रुपए)?\s*(\d[\d,]*(?:\.\d+)?)\s*"
        + nfc(r"(lakhs?|lacs?|crores?|thousand|k\b|लाख|हजार|हज़ार|करोड़|करोड)?"))
_INC = nfc(r"(?:income|earn(?:s|ing|ings)?|salary|wages?|revenue|आय|आमदनी|कमाई|कमाता|कमाती|कमाते|उत्पन्न|वेतन|"
           r"पगार|तनख्वाह|मासिक|कमावतो|कमावते|मिळवतो|मिळवते)")
_ANNUAL = re.compile(nfc(r"annual|yearly|per year|a year|/year|per annum|सालाना|वार्षिक|वर्षाला|प्रति वर्ष"))
_MONTHLY = re.compile(nfc(r"monthly|per month|a month|/month|every month|महीना|महीने|मासिक|महिना|महिन्याला|दरमहा|"
                          r"प्रति माह|प्रतिमाह"))


def _money(num, unit):
    v = float(num.replace(",", ""))
    if unit:
        v *= _UNIT[nfc(unit.lower())]
    return v


def _period(window):
    if _ANNUAL.search(window):
        return 1
    if _MONTHLY.search(window):
        return 12
    return 1


def extract_income(text: str, loose: bool = False) -> Optional[int]:
    """Yearly household income in rupees. loose=True is used when we just asked for income."""
    tl = normalize(text).lower()
    if re.search(r"\b(?:no|zero|nil)\s+income\b", tl) or "कोई आय नहीं" in tl:
        return 0
    patterns = [re.compile(_INC + r"[^\d]{0,30}?" + _AMT), re.compile(_AMT + r"[^\d\n]{0,25}?" + _INC)]
    if loose:
        patterns.append(re.compile(_AMT))
    for i, pat in enumerate(patterns):
        for m in pat.finditer(tl):
            num, unit = m.group(1), m.group(2)
            v = _money(num, unit)
            if not unit and v < 1000:
                continue
            window = tl[max(0, m.start() - 15): m.end() + 30]
            return int(v * _period(window))
    return None


_CLAUSE_CHILD = re.compile(nfc(r"daughter|son\b|child|children|kid|baby|girl|boy|बेटी|बेटा|मुलगी|मुलगा|बच्ची|बच्चा|"
                               r"बच्चे|लड़की|लड़का|पोती|नातू"))


def extract_age(text: str) -> Optional[int]:
    tl = normalize(text).lower()
    pats = [
        r"(?<!\d)(\d{1,3})\s*-?\s*(?:years?|yrs?|yr)[\s-]*old",
        r"\b(?:age|aged)\s*(?:is|of|:|-)?\s*(\d{1,3})(?!\d)",
        r"\bi\s*(?:am|'m|m)\s+(\d{1,3})(?!\d)(?!\s*(?:lakh|k\b|rs|%|thousand|acre))",
        nfc(r"(?:उम्र|आयु|वय|उमर)\s*(?:है|आहे|:|-)?\s*(\d{1,3})(?!\d)"),
        nfc(r"(?<!\d)(\d{1,3})\s*(?:वर्ष|साल|बरस)"),
        r"(?<!\d)(\d{1,3})\s*(?:years?|yrs?)\b(?!\s*(?:of|in|since|ago|experience))",
    ]
    for p in pats:
        for m in re.finditer(p, tl):
            if _CLAUSE_CHILD.search(_before(tl, m.start())):
                continue
            if re.search(r"\bper\s*$", tl[:m.start()]):
                continue
            age = int(m.group(1))
            if 0 < age <= 120:
                return age
    return None


# ----------------------------------------------------------------------------- lexicons
STATES = {
    "maharashtra": ["maharashtra", "महाराष्ट्र", "pune", "pimpri", "chinchwad", "mumbai", "nagpur", "nashik", "thane",
                    "aurangabad", "kolhapur", "solapur", "पुणे", "पुण्य", "मुंबई", "नागपूर", "नाशिक", "ठाणे", "कोल्हापूर"],
    "uttar pradesh": ["uttar pradesh", "उत्तर प्रदेश", "lucknow", "kanpur", "varanasi", "लखनऊ"],
    "bihar": ["bihar", "बिहार", "patna", "पटना"],
    "madhya pradesh": ["madhya pradesh", "मध्य प्रदेश", "bhopal", "indore", "भोपाल", "इंदौर"],
    "rajasthan": ["rajasthan", "राजस्थान", "jaipur", "जयपुर"],
    "gujarat": ["gujarat", "गुजरात", "ahmedabad", "surat", "अहमदाबाद"],
    "karnataka": ["karnataka", "कर्नाटक", "bengaluru", "bangalore", "mysuru"],
    "tamil nadu": ["tamil nadu", "तमिलनाडु", "तमिळनाडू", "chennai", "madurai"],
    "kerala": ["kerala", "केरल", "केरळ"],
    "andhra pradesh": ["andhra pradesh", "आंध्र प्रदेश"],
    "telangana": ["telangana", "तेलंगाना", "तेलंगणा", "hyderabad"],
    "west bengal": ["west bengal", "पश्चिम बंगाल", "kolkata"],
    "odisha": ["odisha", "orissa", "ओडिशा"],
    "punjab": ["punjab", "पंजाब"],
    "haryana": ["haryana", "हरियाणा"],
    "delhi": ["delhi", "दिल्ली"],
    "assam": ["assam", "असम", "आसाम"],
    "jharkhand": ["jharkhand", "झारखंड"],
    "chhattisgarh": ["chhattisgarh", "छत्तीसगढ़", "छत्तीसगढ"],
    "uttarakhand": ["uttarakhand", "उत्तराखंड"],
    "himachal pradesh": ["himachal pradesh", "हिमाचल प्रदेश"],
    "goa": ["goa", "गोवा"],
    "jammu and kashmir": ["jammu", "kashmir", "जम्मू"],
    "tripura": ["tripura"], "manipur": ["manipur"], "meghalaya": ["meghalaya"], "mizoram": ["mizoram"],
    "nagaland": ["nagaland"], "arunachal pradesh": ["arunachal pradesh"], "sikkim": ["sikkim"],
}

OCCUPATIONS = [  # priority order
    ("retired", ["retired", "pensioner", "सेवानिवृत्त", "निवृत्त"]),
    ("govt_employee", ["government employee", "govt employee", "government servant", "government job", "govt job",
                       "civil servant", "सरकारी कर्मचारी", "सरकारी नौकरी", "शासकीय कर्मचारी", "सरकारी नोकर",
                       "सरकारी नोकरी"]),
    ("farmer", ["farmer", "farming", "cultivator", "kisan", "agriculturist", "किसान", "खेती", "शेतकरी", "कृषक",
                "शेती करतो", "शेती करते"]),
    ("student", ["student", "studying", "college", "विद्यार्थी", "विद्यार्थिनी", "छात्र", "छात्रा", "पढ़ाई"]),
    ("artisan", ["artisan", "carpenter", "potter", "blacksmith", "tailor", "weaver", "cobbler", "barber", "goldsmith",
                 "mason", "sculptor", "washerman", "कारीगर", "कारागीर", "बढ़ई", "सुतार", "लोहार", "कुम्हार", "कुंभार",
                 "दर्जी", "शिंपी", "नाई", "न्हावी", "सोनार", "धोबी", "परीट"]),
    ("labourer", ["labour", "labourer", "laborer", "daily wage", "wage worker", "construction worker", "मजदूर",
                  "मजूर", "कामगार", "मोलमजुरी", "दिहाड़ी"]),
    ("business", ["shop", "shopkeeper", "business", "businessman", "entrepreneur", "vendor", "trader", "दुकान",
                  "दुकानदार", "व्यापार", "व्यवसाय", "उद्योग", "धंधा"]),
    ("salaried", ["salaried", "private job", "private company", "नौकरी करता", "नौकरी करती", "नोकरी करतो", "नोकरी करते"]),
    ("homemaker", ["housewife", "homemaker", "गृहिणी"]),
    ("unemployed", ["unemployed", "jobless", "बेरोजगार"]),
]
_START_BIZ = re.compile(r"(?:start|starting|begin|open|set ?up|launch|new)\W+(?:\w+\W+){0,2}$")
_START_BIZ_AFTER = re.compile(nfc(r"शुरू|सुरू|start"))

FLAGS = {
    "has_bank_account": dict(pos=["bank account", "savings account", "bank khata", "बैंक खाता", "बैंक अकाउंट",
                                   "बँक खाते", "बँक खाता", "खाता", "खाते"]),
    "is_bpl": dict(pos=["bpl", "below poverty line", "poverty line", "बीपीएल", "गरीबी रेखा", "दारिद्र्यरेषा",
                        "दारिद्र्य रेषा", "antyodaya", "अंत्योदय"], neg=["above poverty line", "apl", "एपीएल"]),
    "owns_land": dict(pos=["own land", "owns land", "have land", "has land", "farm land", "farmland",
                           "agricultural land", "cultivable land", "land holding", "landholding", "जमीन", "ज़मीन",
                           "जमिन", "शेतजमीन", "भूमि", "7/12"], neg=["landless", "no land", "भूमिहीन", "भूमीहीन"]),
    "has_pucca_house": dict(pos=["pucca house", "pakka house", "own house", "own a house", "have a house",
                                 "पक्का मकान", "पक्का घर", "पक्के घर", "पक्के मकान", "स्वतःचे घर"],
                            neg=["kutcha", "kachcha", "kacha", "homeless", "कच्चा", "कच्चे", "कच्च्या", "बेघर",
                                 "no house", "no home"]),
    "is_income_tax_payer": dict(pos=["income tax", "income-tax", "itr", "tax payer", "taxpayer", "आयकर",
                                     "इनकम टैक्स", "इन्कम टॅक्स"]),
    "has_lpg": dict(pos=["lpg", "gas connection", "gas cylinder", "cooking gas", "गैस कनेक्शन", "गैस सिलेंडर",
                         "गॅस कनेक्शन", "गॅस जोडणी", "एलपीजी", "सिलेंडर", "सिलिंडर"]),
}
DESIRE_FLAGS = {"has_lpg", "has_bank_account", "has_pucca_house"}  # "I want X" => currently does not have X

GENDER = [("female", ["woman", "female", "lady", "widow", "housewife", "homemaker", "महिला", "औरत", "स्त्री",
                       "विधवा", "गृहिणी"]),
          ("male", ["male", "man", "gentleman", "पुरुष", "पुरूष", "आदमी"])]
AREA = [("rural", ["village", "rural", "gaon", "गाँव", "गांव", "गाव", "ग्रामीण", "खेडे", "खेड्यात"]),
        ("urban", ["urban", "city", "town", "metro", "शहर", "शहरी", "नगर"])]
CATEGORY = [("sc", ["scheduled caste", "dalit", "अनुसूचित जाति", "अनुसूचित जाती", "दलित"]),
            ("st", ["scheduled tribe", "tribal", "adivasi", "अनुसूचित जनजाति", "अनुसूचित जमाती", "आदिवासी"]),
            ("obc", ["other backward", "इतर मागास", "पिछड़ा", "पिछडा"]),
            ("general", ["general category", "open category", "general caste", "सामान्य श्रेणी", "सामान्य वर्ग",
                         "खुला प्रवर्ग", "सामान्य प्रवर्ग"])]
_CASTE_TOKEN = re.compile(r"\b(SC|ST|OBC)\b")
_CASTE_LOOSE = re.compile(r"\b(sc|st|obc)\b(?=\s*(?:category|caste|class|वर्ग))|(?:category|caste)\s*(?:is|:)?\s*(sc|st|obc)\b",
                          re.I)

NEEDS = {
    "agriculture": ["farm", "farming", "crop", "kisan", "agriculture", "fertilizer", "खेती", "किसान", "शेतकरी", "शेती", "पीक", "फसल"],
    "housing": ["house", "home", "housing", "shelter", "flat", "construct", "घर", "मकान", "आवास", "घरकुल", "निवारा"],
    "health": ["health", "hospital", "medical", "treatment", "surgery", "स्वास्थ्य", "अस्पताल", "इलाज", "आरोग्य",
               "रुग्णालय", "उपचार"],
    "pension": ["pension", "old age", "retirement", "पेंशन", "पेन्शन", "वृद्धावस्था", "वृद्धापकाळ", "निवृत्तीवेतन"],
    "insurance": ["insurance", "accident cover", "बीमा", "विमा"],
    "education": ["scholarship", "education", "tuition", "fees", "study", "छात्रवृत्ति", "शिष्यवृत्ती", "शिक्षा", "शिक्षण"],
    "business": ["business", "loan", "startup", "enterprise", "self-employment", "mudra", "व्यापार", "कर्ज", "ऋण", "लोन", "व्यवसाय"],
    "women": ["for women", "women scheme", "women's scheme", "महिलाओं", "महिलांसाठी", "लाडकी"],
    "banking": ["open an account", "zero balance", "जन धन", "जनधन", "खाता खोलना", "खाते उघडा"],
    "girl_child": ["for my daughter", "for daughter", "girl child scheme", "बेटी के लिए", "मुलीसाठी", "सुकन्या", "sukanya"],
    "skill": ["skill", "training", "toolkit", "कौशल", "प्रशिक्षण"],
    "cooking_fuel": ["lpg", "gas cylinder", "cooking gas", "गैस", "गॅस", "सिलेंडर"],
    "senior": ["senior citizen", "elderly", "old age", "बुजुर्ग", "ज्येष्ठ", "वृद्ध"],
    "income_support": ["financial help", "income support", "financial assistance", "monthly assistance", "आर्थिक मदद",
                       "आर्थिक सहाय्य", "सहायता राशि"],
}

INTENTS = {
    "documents": ["document", "documents", "papers", "paperwork", "required docs", "दस्तावेज", "दस्तावेज़", "कागज",
                  "कागदपत्र", "कागदपत्रे", "डॉक्यूमेंट"],
    "apply": ["apply", "application", "register", "registration", "how to get", "आवेदन", "अर्ज", "कैसे", "कसा", "कसे",
              "नोंदणी", "पंजीकरण"],
    "why": ["why", "reason", "explain", "क्यों", "कारण", "का नहीं", "का नाही"],
}


# ----------------------------------------------------------------------------- extraction
def _first_pos(tl, table):
    for value, terms in table:
        if find_terms(tl, terms):
            return value
    return None


def extract_profile(text: str) -> Dict[str, Any]:
    t0 = normalize(text)
    tl = t0.lower()
    out: Dict[str, Any] = {}

    age = extract_age(t0)
    if age is not None:
        out["age"] = age
    inc = extract_income(t0)
    if inc is not None:
        out["annual_income"] = inc

    g = _first_pos(tl, GENDER)
    if g:
        out["gender"] = g
    a = _first_pos(tl, AREA)
    if a:
        out["area"] = a

    # state: earliest match wins
    best = None
    for state, aliases in STATES.items():
        for s, e in find_terms(tl, aliases):
            if best is None or (s, -(e - s)) < best[:2]:
                best = (s, -(e - s), state)
    if best:
        out["state"] = best[2]

    # social category
    m = _CASTE_TOKEN.search(t0) or _CASTE_LOOSE.search(t0)
    if m:
        out["category"] = next(x for x in m.groups() if x).lower()
    else:
        c = _first_pos(tl, CATEGORY)
        if c:
            out["category"] = c

    # occupation
    for occ, terms in OCCUPATIONS:
        found = False
        for s, e in find_terms(tl, terms):
            if _negated(tl, s, e):
                continue
            if occ == "business" and (_START_BIZ.search(_before(tl, s)) or _START_BIZ_AFTER.search(_after(tl, e, 15))):
                continue
            found = True
            break
        if found:
            out["occupation"] = occ
            break

    # boolean facts
    for attr, spec in FLAGS.items():
        if spec.get("neg") and find_terms(tl, spec["neg"]):
            out[attr] = False
            continue
        spans = find_terms(tl, spec["pos"])
        if spans:
            s, e = spans[0]
            neg = _negated(tl, s, e)
            if attr in DESIRE_FLAGS and _desired(tl, s, e):
                neg = True
            out[attr] = not neg

    # land size
    m = re.search(nfc(r"(\d+(?:\.\d+)?)\s*(acres?|hectares?|ha\b|एकड़|एकड|एकर|हेक्टेयर|हेक्टर)"), tl)
    if m and not (out.get("owns_land") is False):
        v = float(m.group(1))
        if m.group(2).startswith(("hect", "ha", "हेक्ट")):
            v *= 2.47
        out["land_acres"] = round(v, 2)
        out["owns_land"] = True

    # daughter aged <= 10 (Sukanya Samriddhi)
    for s, e in find_terms(tl, ["daughter", "girl child", "baby girl", "बेटी", "मुलगी", "बच्ची"]):
        if _negated(tl, s, e):
            out["has_girl_child_under_10"] = False
            break
        win_after = tl[e:e + 30]
        win_before = tl[max(0, s - 18):s]
        mm = (re.search(r"(?:aged?|of|उम्र|वय)\s*(\d{1,2})(?!\d)\s*(months?|महीने|महिने)?", win_after)
              or re.search(nfc(r"(\d{1,2})(?!\d)\s*-?\s*(?:years?|yrs?|year|साल|वर्ष)?\s*-?\s*(?:old|की|ची|चा)?\s*(months?|महीने)?\W*$"), win_before)
              or re.search(nfc(r"(\d{1,2})\s*(?:years?|yrs?|साल|वर्ष)"), win_after))
        if mm:
            is_month = bool(mm.groups()[-1]) if mm.lastindex and mm.lastindex >= 2 else False
            out["has_girl_child_under_10"] = True if is_month else int(mm.group(1)) <= 10
            break
        if re.search(r"new\s*born|newborn|नवजात", tl):
            out["has_girl_child_under_10"] = True
            break
    return out


def extract_needs(text: str) -> Set[str]:
    tl = normalize(text).lower()
    return {need for need, terms in NEEDS.items() if find_terms(tl, terms)}


def detect_intents(text: str) -> Set[str]:
    tl = normalize(text).lower()
    return {i for i, terms in INTENTS.items() if find_terms(tl, terms)}


# ----------------------------------------------------------------------------- answers to our questions
_YES = {"yes", "y", "yeah", "yep", "yup", "ok", "okay", "sure", "haan", "han", "ha", "हाँ", "हां", "हा", "जी",
        "होय", "हो", "आहे", "है", "हैं", "correct"}
_NO = {"no", "n", "nope", "nahi", "nahin", "नहीं", "नही", "नाही", "नको", "ना", "न", "don't", "dont", "not"}
BOOL_ATTRS = {"is_bpl", "owns_land", "has_pucca_house", "has_bank_account", "is_income_tax_payer", "has_lpg",
              "has_girl_child_under_10"}


def parse_pending(attr: str, text: str) -> Any:
    """Interpret a short reply to the question we just asked about `attr`."""
    t0 = normalize(text)
    tl = t0.lower()
    if attr in BOOL_ATTRS:
        toks = {w.strip(".,!?;:।\"'()") for w in nfc(tl).split()}
        if toks & _NO:
            return False
        if toks & _YES:
            return True
        return None
    if attr == "age":
        m = re.search(r"(?<!\d)(\d{1,3})(?!\d)", tl)
        return int(m.group(1)) if m and 0 < int(m.group(1)) <= 120 else None
    if attr == "annual_income":
        return extract_income(t0, loose=True)
    return None
