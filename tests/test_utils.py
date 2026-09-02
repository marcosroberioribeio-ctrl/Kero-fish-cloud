import unittest
from datetime import date

from kero_fish.utils import moeda, norm_key, to_float, to_iso_date


class UtilsTests(unittest.TestCase):
    def test_moeda_brasileira(self):
        self.assertEqual(moeda(1234.56), "R$ 1.234,56")
        self.assertEqual(moeda(0), "R$ 0,00")

    def test_to_float_brasileiro(self):
        self.assertAlmostEqual(to_float("R$ 1.234,56"), 1234.56)
        self.assertAlmostEqual(to_float("39,90"), 39.90)

    def test_to_iso_date(self):
        self.assertEqual(to_iso_date("02/09/2026"), "2026-09-02")
        self.assertEqual(to_iso_date(date(2026, 9, 2)), "2026-09-02")

    def test_norm_key(self):
        self.assertEqual(norm_key("Filé de Camarão GG"), "file_de_camarao_gg")


if __name__ == "__main__":
    unittest.main()
