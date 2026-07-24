from datetime import date
import unittest

from maya_calendar import convert_birth_date


class CalendarConversionTests(unittest.TestCase):
    def test_maya_epoch_checkpoint(self):
        result = convert_birth_date(date(2012, 12, 21))
        self.assertEqual(result.long_count_text, "13.0.0.0.0")
        self.assertEqual(result.tzolkin_number, 4)
        self.assertEqual(result.tzolkin_maya_name, "Ajaw")
        self.assertEqual((result.haab_day, result.haab_month), (3, "K'ank'in"))
        self.assertEqual(result.product_no, 4)

    def test_reference_demo_date_maps_to_jaguar_product(self):
        result = convert_birth_date(date(2026, 7, 15))
        self.assertEqual(result.long_count_text, "13.0.13.13.14")
        self.assertEqual(result.aztec_name, "Ocelotl")
        self.assertEqual(result.tzolkin_number, 5)
        self.assertEqual((result.haab_day, result.haab_month), (7, "Xul"))
        self.assertEqual(result.night_lord, 4)
        self.assertEqual(result.product_no, 18)

    def test_current_checkpoint(self):
        result = convert_birth_date(date(2026, 7, 19))
        self.assertEqual(result.long_count_text, "13.0.13.13.18")
        self.assertEqual(result.tzolkin_number, 9)
        self.assertEqual(result.tzolkin_maya_name, "Etz'nab'")
        self.assertEqual(result.product_no, 2)


if __name__ == "__main__":
    unittest.main()
