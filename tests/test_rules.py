import unittest
from app.rules import FALSE, TRUE, UNKNOWN, evaluate, missing_attrs, validate


def leaf(a, o, v):
    return {"attr": a, "op": o, "value": v}


class RulesTest(unittest.TestCase):
    def test_leaf_ops(self):
        self.assertEqual(evaluate(leaf("age", "gte", 60), {"age": 60}).status, TRUE)
        self.assertEqual(evaluate(leaf("age", "between", [18, 40]), {"age": 41}).status, FALSE)
        self.assertEqual(evaluate(leaf("category", "in", ["sc", "st"]), {"category": "SC"}).status, TRUE)
        self.assertEqual(evaluate(leaf("occupation", "not_in", ["govt_employee"]), {"occupation": "farmer"}).status, TRUE)

    def test_unknown_is_not_false(self):
        self.assertEqual(evaluate(leaf("age", "gte", 60), {}).status, UNKNOWN)

    def test_all_any_three_valued(self):
        rule = {"all": [leaf("age", "gte", 18), leaf("is_bpl", "eq", True)]}
        self.assertEqual(evaluate(rule, {"age": 10}).status, FALSE)            # one FALSE decides
        self.assertEqual(evaluate(rule, {"age": 30}).status, UNKNOWN)          # other still unknown
        self.assertEqual(evaluate(rule, {"age": 30, "is_bpl": True}).status, TRUE)
        anyr = {"any": [leaf("is_bpl", "eq", True), leaf("age", "gte", 70)]}
        self.assertEqual(evaluate(anyr, {"age": 75}).status, TRUE)
        self.assertEqual(evaluate(anyr, {"age": 40}).status, UNKNOWN)
        self.assertEqual(evaluate(anyr, {"age": 40, "is_bpl": False}).status, FALSE)

    def test_missing_attrs_ignores_decided_branches(self):
        rule = {"all": [leaf("age", "gte", 18), leaf("is_bpl", "eq", True)]}
        self.assertEqual(missing_attrs(evaluate(rule, {"age": 10})), [])       # already ineligible
        self.assertEqual(missing_attrs(evaluate(rule, {"age": 30})), ["is_bpl"])

    def test_validate(self):
        self.assertEqual(validate(leaf("age", "gte", 1), {"age"}), [])
        self.assertTrue(validate(leaf("agee", "gte", 1), {"age"}))
        self.assertTrue(validate(leaf("age", "approx", 1), {"age"}))


if __name__ == "__main__":
    unittest.main()
