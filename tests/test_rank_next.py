import unittest
from rank_next import safe_int, safe_float, is_truthy, game_key, compute_score


class TestParsers(unittest.TestCase):
    def test_safe_int(self):
        self.assertEqual(safe_int("1,234"), 1234)
        self.assertEqual(safe_int("bad", default=7), 7)

    def test_safe_float(self):
        self.assertEqual(safe_float("3.5"), 3.5)
        self.assertIsNone(safe_float(""))

    def test_is_truthy(self):
        self.assertTrue(is_truthy("Yes"))
        self.assertTrue(is_truthy("1"))
        self.assertFalse(is_truthy("0"))


class TestGameKey(unittest.TestCase):
    def test_a_pattern(self):
        self.assertEqual(game_key("G", "/a12345/"), "G__a12345")

    def test_query_id(self):
        self.assertEqual(game_key("G", "https://x?achievementid=678"), "G__id678")

    def test_fallback(self):
        k = game_key("G", "https://example.com/foo/bar")
        self.assertTrue(k.startswith("G__example.com/"))


class TestComputeScore(unittest.TestCase):
    def make_g(self):
        return {
            "earned_ach": 0, "earned_gs": 0, "earned_ta": 0, "earned_dlc_ach": 0,
            "locked_ach_total": 0, "locked_gs_total": 0, "locked_ta_total": 0, "locked_dlc_ach": 0,
            "locked_ach_unach": 0, "locked_gs_unach": 0, "locked_ta_unach": 0, "locked_dlc_unach": 0,
            "earned_ratios": [], "locked_ratios_achievable": []
        }

    def test_compute_basic(self):
        g = self.make_g()
        g["earned_gs"] = 100
        g["locked_ach_total"] = 2
        g["locked_gs_total"] = 100
        g["locked_ratios_achievable"] = [2.0, 4.0]
        res = compute_score("G", g)
        self.assertIsNotNone(res)
        self.assertIn("score", res)
        self.assertIn("breakdown", res)
        self.assertEqual(res["remaining_ach"], 2)

    def test_compute_finished(self):
        g = self.make_g()
        g["earned_gs"] = 200
        g["locked_ach_total"] = 0
        g["locked_gs_total"] = 0
        res = compute_score("G", g)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
