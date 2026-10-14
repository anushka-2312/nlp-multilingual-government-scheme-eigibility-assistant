import unittest
from app.nlu import detect_language, extract_income, extract_needs, extract_profile


class NLUTest(unittest.TestCase):
    def test_english_profile(self):
        p = extract_profile("I am a 45 year old farmer from Pune. I own 2 acres of land and my family income is "
                            "1.5 lakh per year. I have a bank account and a daughter aged 5.")
        self.assertEqual((p["age"], p["occupation"], p["state"]), (45, "farmer", "maharashtra"))
        self.assertEqual((p["annual_income"], p["land_acres"]), (150000, 2.0))
        self.assertTrue(p["owns_land"] and p["has_bank_account"] and p["has_girl_child_under_10"])

    def test_hindi_profile(self):
        p = extract_profile("मैं 65 साल का किसान हूँ। मेरे पास 2 एकड़ जमीन है और मेरी वार्षिक आय 1.5 लाख रुपये है।")
        self.assertEqual((p["age"], p["occupation"], p["annual_income"]), (65, "farmer", 150000))

    def test_marathi_profile_with_devanagari_digits(self):
        p = extract_profile("मी ३५ वर्षांची महिला आहे, पुण्यात राहते. माझे वार्षिक उत्पन्न २ लाख आहे")
        self.assertEqual((p["age"], p["gender"], p["state"], p["annual_income"]), (35, "female", "maharashtra", 200000))

    def test_monthly_income_is_annualised(self):
        self.assertEqual(extract_income("I earn 15000 per month"), 180000)
        self.assertEqual(extract_income("monthly income 20k"), 240000)

    def test_negation_and_desire(self):
        self.assertFalse(extract_profile("I don't have a bank account")["has_bank_account"])
        self.assertFalse(extract_profile("मेरा बैंक खाता नहीं है")["has_bank_account"])
        self.assertFalse(extract_profile("I want an LPG connection")["has_lpg"])
        self.assertFalse(extract_profile("I do not pay income tax")["is_income_tax_payer"])
        self.assertNotIn("occupation", extract_profile("I am not a farmer"))

    def test_child_age_not_taken_as_own_age(self):
        p = extract_profile("my daughter is 5 years old and I am 38")
        self.assertEqual(p["age"], 38)
        self.assertTrue(p["has_girl_child_under_10"])

    def test_category_tokens(self):
        self.assertEqual(extract_profile("I belong to SC category")["category"], "sc")
        self.assertEqual(extract_profile("I am OBC")["category"], "obc")

    def test_needs_and_language(self):
        self.assertIn("housing", extract_needs("I need help building a house"))
        self.assertIn("pension", extract_needs("मुझे पेंशन चाहिए"))
        self.assertEqual(detect_language("मी शेतकरी आहे"), "mr")
        self.assertEqual(detect_language("मैं किसान हूँ"), "hi")
        self.assertEqual(detect_language("hello"), "en")


if __name__ == "__main__":
    unittest.main()
