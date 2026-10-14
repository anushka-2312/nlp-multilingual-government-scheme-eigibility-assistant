"""All user-facing text in English (en), Hindi (hi) and Marathi (mr)."""
import unicodedata

LANGS = ("en", "hi", "mr")


def _L(en, hi, mr):
    return {"en": en, "hi": hi, "mr": mr}


STRINGS = {
    "welcome": _L(
        "Namaste! 🙏 I can help you find government schemes you may be eligible for.\n"
        "Tell me about yourself in your own words — e.g. your age, state, occupation, family income, "
        "and what help you need (housing, health, pension, loan, scholarship…).\n"
        "You can write in English, हिन्दी or मराठी.",
        "नमस्ते! 🙏 मैं आपके लिए उपयुक्त सरकारी योजनाएँ खोजने में मदद कर सकता हूँ।\n"
        "अपने बारे में अपने शब्दों में बताइए — जैसे उम्र, राज्य, पेशा, पारिवारिक आय और किस तरह की मदद चाहिए "
        "(आवास, स्वास्थ्य, पेंशन, ऋण, छात्रवृत्ति…)।\nआप English, हिन्दी या मराठी में लिख सकते हैं।",
        "नमस्कार! 🙏 तुमच्यासाठी योग्य सरकारी योजना शोधण्यात मी मदत करू शकतो.\n"
        "तुमच्याबद्दल तुमच्या शब्दांत सांगा — उदा. वय, राज्य, व्यवसाय, कौटुंबिक उत्पन्न आणि कोणती मदत हवी "
        "(घर, आरोग्य, पेन्शन, कर्ज, शिष्यवृत्ती…).\nतुम्ही English, हिन्दी किंवा मराठीत लिहू शकता."),
    "learned": _L("Noted: {items}", "समझ गया: {items}", "समजले: {items}"),
    "eligible_h": _L("You appear to be ELIGIBLE for:", "आप इन योजनाओं के लिए पात्र प्रतीत होते हैं:",
                     "तुम्ही या योजनांसाठी पात्र दिसता:"),
    "possible_h": _L("You MAY be eligible — I need a little more information:",
                     "आप पात्र हो सकते हैं — कुछ और जानकारी चाहिए:",
                     "तुम्ही पात्र असू शकता — आणखी थोडी माहिती हवी:"),
    "not_h": _L("NOT eligible (with reasons):", "पात्र नहीं (कारण सहित):", "पात्र नाही (कारणांसह):"),
    "no_match": _L("I couldn't find a matching scheme yet. Tell me more about yourself or the help you need.",
                   "अभी कोई मेल खाती योजना नहीं मिली। अपने बारे में या ज़रूरत की मदद के बारे में और बताइए।",
                   "अजून जुळणारी योजना सापडली नाही. तुमच्याबद्दल किंवा हव्या असलेल्या मदतीबद्दल अधिक सांगा."),
    "tip": _L("Tip: ask “documents for <scheme>” or “how to apply for <scheme>”.",
              "सुझाव: “<योजना> के दस्तावेज़” या “<योजना> के लिए आवेदन कैसे करें” पूछें।",
              "सूचना: “<योजना> कागदपत्रे” किंवा “<योजना> साठी अर्ज कसा करायचा” विचारा."),
    "still_needed": _L("Still needed: {items}", "अभी चाहिए: {items}", "अजून हवे: {items}"),
    "hidden": _L("{n} scheme(s) not shown — say “show all”.", "{n} योजना नहीं दिखाई गईं — “सभी दिखाओ” कहें।",
                 "{n} योजना दाखवल्या नाहीत — “सर्व दाखवा” म्हणा."),
    "docs_h": _L("📄 Documents required for {name}:", "📄 {name} के लिए आवश्यक दस्तावेज़:",
                 "📄 {name} साठी आवश्यक कागदपत्रे:"),
    "apply_h": _L("📝 How to apply for {name}:", "📝 {name} के लिए आवेदन कैसे करें:",
                  "📝 {name} साठी अर्ज कसा करावा:"),
    "step1": _L("Keep the documents listed above ready (originals + photocopies).",
                "ऊपर दिए दस्तावेज़ तैयार रखें (मूल + फोटोकॉपी)।",
                "वर दिलेली कागदपत्रे तयार ठेवा (मूळ + झेरॉक्स)."),
    "step_online": _L("Apply online at: {url}", "ऑनलाइन आवेदन करें: {url}", "ऑनलाइन अर्ज करा: {url}"),
    "step_offline": _L("Or apply in person at: {where}", "या यहाँ जाकर आवेदन करें: {where}",
                       "किंवा येथे जाऊन अर्ज करा: {where}"),
    "step_track": _L("Note the application/acknowledgement number and track the status; follow up if there is no update.",
                     "आवेदन/पावती क्रमांक नोट करें और स्थिति देखते रहें; अपडेट न मिले तो फॉलो-अप करें।",
                     "अर्ज/पावती क्रमांक नोंदवा आणि स्थिती तपासत रहा; अपडेट न मिळाल्यास पाठपुरावा करा."),
    "disclaimer": _L("ℹ️ Guidance based on simplified rules. The concerned department makes the final decision — "
                     "please verify on the official portal.",
                     "ℹ️ यह सरल नियमों पर आधारित मार्गदर्शन है। अंतिम पात्रता संबंधित विभाग तय करता है — "
                     "कृपया आधिकारिक पोर्टल पर जाँचें।",
                     "ℹ️ हे सोप्या नियमांवर आधारित मार्गदर्शन आहे. अंतिम निर्णय संबंधित विभाग घेतो — "
                     "कृपया अधिकृत पोर्टलवर तपासा."),
    "which_scheme": _L("Which scheme do you mean? Mention its name, e.g. “documents for PM-KISAN”.",
                       "आप किस योजना के बारे में पूछ रहे हैं? नाम लिखें, जैसे “पीएम-किसान के दस्तावेज़”।",
                       "कोणत्या योजनेबद्दल विचारत आहात? नाव लिहा, उदा. “पीएम-किसान कागदपत्रे”."),
    "reset": _L("Okay, starting fresh.", "ठीक है, नए सिरे से शुरू करते हैं।", "ठीक आहे, नव्याने सुरू करूया."),
    "skip_hint": _L("(Say “skip” to see results with what I already know.)",
                    "(जो जानकारी है उसी से नतीजे देखने के लिए “skip” लिखें।)",
                    "(आहे त्या माहितीवर निकाल पाहण्यासाठी “skip” लिहा.)"),
    "any_of": _L("Any ONE of these:", "इनमें से कोई एक:", "यापैकी कोणताही एक:"),
    "yes": _L("Yes", "हाँ", "होय"),
    "no": _L("No", "नहीं", "नाही"),
    "you": _L(" (you: {v})", " (आप: {v})", " (तुम्ही: {v})"),
    "unk": _L(" (not provided yet)", " (अभी पता नहीं)", " (अजून माहीत नाही)"),
    "req_bool": _L("{label}: {v} (required)", "{label}: {v} (आवश्यक)", "{label}: {v} (आवश्यक)"),
    "no_docs": _L("No document list available.", "दस्तावेज़ सूची उपलब्ध नहीं।", "कागदपत्र यादी उपलब्ध नाही."),
}

OPS = {
    "gte": _L("{label} must be at least {v}", "{label} कम से कम {v} होना चाहिए", "{label} किमान {v} असावे"),
    "lte": _L("{label} must be at most {v}", "{label} अधिकतम {v} होना चाहिए", "{label} कमाल {v} असावे"),
    "gt": _L("{label} must be more than {v}", "{label} {v} से अधिक होना चाहिए", "{label} {v} पेक्षा जास्त असावे"),
    "lt": _L("{label} must be less than {v}", "{label} {v} से कम होना चाहिए", "{label} {v} पेक्षा कमी असावे"),
    "eq": _L("{label} must be {v}", "{label} {v} होना चाहिए", "{label} {v} असावे"),
    "ne": _L("{label} must not be {v}", "{label} {v} नहीं होना चाहिए", "{label} {v} नसावे"),
    "in": _L("{label} must be one of: {v}", "{label} इनमें से एक होना चाहिए: {v}", "{label} यापैकी एक असावे: {v}"),
    "not_in": _L("{label} must not be: {v}", "{label} ये नहीं होना चाहिए: {v}", "{label} हे नसावे: {v}"),
    "between": _L("{label} must be between {lo} and {hi}", "{label} {lo} और {hi} के बीच होना चाहिए",
                  "{label} {lo} ते {hi} दरम्यान असावे"),
}

ATTR_LABELS = {
    "age": _L("Age", "उम्र", "वय"),
    "gender": _L("Gender", "लिंग", "लिंग"),
    "state": _L("State", "राज्य", "राज्य"),
    "area": _L("Area", "क्षेत्र", "क्षेत्र"),
    "annual_income": _L("Annual family income", "वार्षिक पारिवारिक आय", "वार्षिक कौटुंबिक उत्पन्न"),
    "occupation": _L("Occupation", "पेशा", "व्यवसाय"),
    "category": _L("Social category", "सामाजिक श्रेणी", "सामाजिक प्रवर्ग"),
    "is_bpl": _L("BPL household", "बीपीएल परिवार", "बीपीएल कुटुंब"),
    "owns_land": _L("Owns agricultural land", "कृषि भूमि का स्वामित्व", "शेतजमिनीची मालकी"),
    "land_acres": _L("Land (acres)", "भूमि (एकड़)", "जमीन (एकर)"),
    "has_pucca_house": _L("Owns a pucca house", "पक्का मकान है", "पक्के घर आहे"),
    "has_bank_account": _L("Has a bank account", "बैंक खाता है", "बँक खाते आहे"),
    "is_income_tax_payer": _L("Pays income tax", "आयकर दाता", "आयकर भरतो"),
    "has_lpg": _L("Has LPG connection", "एलपीजी कनेक्शन है", "एलपीजी जोडणी आहे"),
    "has_girl_child_under_10": _L("Has daughter aged 10 or below", "10 वर्ष तक की बेटी है", "१० वर्षांपर्यंतची मुलगी आहे"),
}

QUESTIONS = {
    "age": _L("How old are you?", "आपकी उम्र कितनी है?", "तुमचे वय किती आहे?"),
    "gender": _L("Are you male or female?", "आप पुरुष हैं या महिला?", "तुम्ही पुरुष आहात की महिला?"),
    "state": _L("Which state do you live in?", "आप किस राज्य में रहते हैं?", "तुम्ही कोणत्या राज्यात राहता?"),
    "area": _L("Do you live in a village (rural) or a city/town (urban)?",
               "आप गाँव (ग्रामीण) में रहते हैं या शहर में?", "तुम्ही गावात (ग्रामीण) राहता की शहरात?"),
    "annual_income": _L("What is your family's total yearly income (approximately)?",
                        "आपके परिवार की कुल वार्षिक आय लगभग कितनी है?",
                        "तुमच्या कुटुंबाचे वार्षिक उत्पन्न साधारण किती आहे?"),
    "occupation": _L("What do you do for a living? (farmer, student, artisan, business, salaried, labourer, homemaker…)",
                     "आप क्या काम करते हैं? (किसान, विद्यार्थी, कारीगर, व्यापार, नौकरी, मजदूर, गृहिणी…)",
                     "तुम्ही काय काम करता? (शेतकरी, विद्यार्थी, कारागीर, व्यवसाय, नोकरी, मजूर, गृहिणी…)"),
    "category": _L("Which category do you belong to — General, OBC, SC or ST?",
                   "आप किस श्रेणी से हैं — सामान्य, OBC, SC या ST?",
                   "तुम्ही कोणत्या प्रवर्गात येता — सामान्य, OBC, SC की ST?"),
    "is_bpl": _L("Does your household have a BPL card (below poverty line)?",
                 "क्या आपके परिवार के पास बीपीएल कार्ड है (गरीबी रेखा से नीचे)?",
                 "तुमच्या कुटुंबाकडे बीपीएल कार्ड आहे का (दारिद्र्यरेषेखालील)?"),
    "owns_land": _L("Do you own agricultural land?", "क्या आपके पास खेती की ज़मीन है?",
                    "तुमच्याकडे शेतजमीन आहे का?"),
    "has_pucca_house": _L("Do you own a pucca (permanent, concrete) house?",
                          "क्या आपके पास पक्का मकान है?", "तुमच्याकडे पक्के घर आहे का?"),
    "has_bank_account": _L("Do you have a bank account?", "क्या आपका बैंक खाता है?", "तुमचे बँक खाते आहे का?"),
    "is_income_tax_payer": _L("Do you (or anyone in your household) pay income tax?",
                              "क्या आप (या आपके परिवार में कोई) आयकर देते हैं?",
                              "तुम्ही (किंवा कुटुंबातील कोणी) आयकर भरता का?"),
    "has_lpg": _L("Does your household already have an LPG gas connection?",
                  "क्या आपके घर में पहले से एलपीजी गैस कनेक्शन है?",
                  "तुमच्या घरी आधीच एलपीजी गॅस जोडणी आहे का?"),
    "has_girl_child_under_10": _L("Do you have a daughter aged 10 or below?",
                                  "क्या आपकी 10 वर्ष या उससे कम उम्र की बेटी है?",
                                  "तुम्हाला १० वर्षे किंवा त्यापेक्षा लहान मुलगी आहे का?"),
}

VALUES = {
    "gender": {"male": _L("Male", "पुरुष", "पुरुष"), "female": _L("Female", "महिला", "महिला")},
    "category": {"general": _L("General", "सामान्य", "सामान्य"),
                 "obc": _L("OBC", "अन्य पिछड़ा वर्ग (OBC)", "इतर मागासवर्ग (OBC)"),
                 "sc": _L("SC", "अनुसूचित जाति (SC)", "अनुसूचित जाती (SC)"),
                 "st": _L("ST", "अनुसूचित जनजाति (ST)", "अनुसूचित जमाती (ST)")},
    "area": {"rural": _L("Rural", "ग्रामीण", "ग्रामीण"), "urban": _L("Urban", "शहरी", "शहरी")},
    "occupation": {
        "farmer": _L("Farmer", "किसान", "शेतकरी"), "student": _L("Student", "विद्यार्थी", "विद्यार्थी"),
        "artisan": _L("Artisan", "कारीगर", "कारागीर"), "business": _L("Business owner", "व्यवसायी", "व्यावसायिक"),
        "salaried": _L("Salaried", "वेतनभोगी", "पगारदार"),
        "govt_employee": _L("Government employee", "सरकारी कर्मचारी", "सरकारी कर्मचारी"),
        "labourer": _L("Labourer", "मजदूर", "मजूर"), "homemaker": _L("Homemaker", "गृहिणी", "गृहिणी"),
        "unemployed": _L("Unemployed", "बेरोजगार", "बेरोजगार"), "retired": _L("Retired", "सेवानिवृत्त", "निवृत्त"),
    },
}

MONEY_ATTRS = {"annual_income"}


def t(key, lang, **kw):
    entry = STRINGS[key]
    s = entry.get(lang) or entry["en"]
    return s.format(**kw) if kw else s


def attr_label(attr, lang):
    e = ATTR_LABELS.get(attr)
    return (e.get(lang) or e["en"]) if e else attr


def question(attr, lang):
    e = QUESTIONS[attr]
    return e.get(lang) or e["en"]


def fmt_inr(n):
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if n < 0 else "") + "₹" + s


def fmt_value(attr, v, lang):
    if isinstance(v, bool):
        return t("yes" if v else "no", lang)
    if attr in MONEY_ATTRS and isinstance(v, (int, float)):
        return fmt_inr(v)
    if attr in VALUES and isinstance(v, str) and v in VALUES[attr]:
        return VALUES[attr][v].get(lang) or VALUES[attr][v]["en"]
    if attr == "state" and isinstance(v, str):
        return v.title()
    return str(v)


def op_text(op, lang, **kw):
    e = OPS[op]
    return (e.get(lang) or e["en"]).format(**kw)


def nfc(s):
    return unicodedata.normalize("NFC", s)
