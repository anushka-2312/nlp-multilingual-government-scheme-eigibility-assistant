import unittest
from app.dialogue import Assistant, Session
from app.i18n import ATTR_LABELS, LANGS, QUESTIONS
from app.rules import validate
from app.schemes import Catalog

BOT = Assistant()


def status(profile, scheme_id):
    c = BOT.catalog
    return c.evaluate(c.get(scheme_id), profile)["status"]


class CatalogDataTest(unittest.TestCase):
    def test_all_rules_valid_and_complete(self):
        cat = Catalog()
        attrs = set(ATTR_LABELS)
        for s in cat.schemes:
            self.assertEqual(validate(s["eligibility"], attrs), [], s["id"])
            for lang in LANGS:
                self.assertTrue(s["name"][lang] and s["summary"][lang], (s["id"], lang))
            for d in s["documents"]:
                self.assertIn(d, cat.documents)
            for ch in s["apply"]["offline"]:
                self.assertIn(ch, cat.channels)
            self.assertTrue(s["apply"]["portal"].startswith("https://"))

    def test_every_attr_has_question_in_all_languages(self):
        cat = Catalog()
        used = set()

        def walk(n):
            if "attr" in n:
                used.add(n["attr"])
            for k in ("all", "any"):
                for c in n.get(k, []):
                    walk(c)
        for s in cat.schemes:
            walk(s["eligibility"])
        for a in used:
            self.assertEqual(set(QUESTIONS[a]), set(LANGS), a)


class EligibilityTest(unittest.TestCase):
    def test_old_age_pension(self):
        self.assertEqual(status({"age": 65, "is_bpl": True}, "ignoaps"), "true")
        self.assertEqual(status({"age": 55, "is_bpl": True}, "ignoaps"), "false")
        self.assertEqual(status({"age": 65}, "ignoaps"), "unknown")

    def test_ladki_bahin_boundaries(self):
        base = {"state": "maharashtra", "gender": "female", "age": 30, "annual_income": 250000, "is_income_tax_payer": False}
        self.assertEqual(status(base, "ladki_bahin"), "true")
        self.assertEqual(status({**base, "annual_income": 250001}, "ladki_bahin"), "false")
        self.assertEqual(status({**base, "state": "bihar"}, "ladki_bahin"), "false")

    def test_pm_kisan_exclusions(self):
        base = {"owns_land": True, "is_income_tax_payer": False, "occupation": "farmer"}
        self.assertEqual(status(base, "pm_kisan"), "true")
        self.assertEqual(status({**base, "occupation": "govt_employee"}, "pm_kisan"), "false")


class DialogueTest(unittest.TestCase):
    def test_english_flow_with_followup_and_documents(self):
        s = Session()
        r = BOT.handle(s, "I am a 70 year old woman from a village, BPL family, no bank account")
        ids = {x["id"]: x["status"] for x in r["results"]}
        self.assertEqual(ids.get("pmjay"), "true")
        self.assertEqual(ids.get("pmjdy"), "true")
        r = BOT.handle(s, "documents for ayushman")
        self.assertIn("Documents required", r["reply"])
        self.assertIn("Aadhaar", r["reply"])

    def test_pending_question_answer_is_used(self):
        s = Session()
        BOT.handle(s, "I am 30 and I need a house")
        self.assertIsNotNone(s.pending)
        asked = s.pending
        BOT.handle(s, "35")  # bare number answers age/income-style questions only
        self.assertIn(asked, s.asked)

    def test_hindi_reply_is_devanagari_and_marathi_distinct(self):
        r = BOT.handle(Session(), "मैं 65 साल का हूँ, बीपीएल परिवार से, मुझे पेंशन चाहिए")
        self.assertEqual(r["lang"], "hi")
        self.assertIn("पात्र", r["reply"])
        r = BOT.handle(Session(), "माझे वय ६५ आहे, मी बीपीएल कुटुंबातील आहे, मला पेन्शन पाहिजे")
        self.assertEqual(r["lang"], "mr")

    def test_scheme_name_is_not_read_as_occupation(self):
        s = Session()
        BOT.handle(s, "documents for PM-KISAN")
        self.assertNotIn("occupation", s.profile)

    def test_apply_guidance_and_reset(self):
        s = Session()
        r = BOT.handle(s, "how to apply for mudra")
        self.assertIn("mudra.org.in", r["reply"])
        BOT.handle(s, "reset")
        self.assertEqual(s.profile, {})

    def test_unknown_input_gives_welcome(self):
        self.assertIn("Namaste", BOT.handle(Session(), "hello")["reply"])


if __name__ == "__main__":
    unittest.main()
