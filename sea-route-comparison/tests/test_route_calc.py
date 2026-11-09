import unittest

from route_calc import compare, great_circle, rhumb_line


class TestCourseExample(unittest.TestCase):
    def test_results(self):
        result = compare(40, -30, 50, -20)
        self.assertAlmostEqual(result["Ортодромия (сфера)"].distance_km, 1359.254526, places=5)
        self.assertAlmostEqual(result["Локсодромия (сфера)"].distance_km, 1360.121891, places=5)
        self.assertAlmostEqual(result["Геодезическая (WGS 84)"].distance_km, 1359.994883, places=5)
        self.assertAlmostEqual(result["Ортодромия (сфера)"].initial_bearing_deg, 31.813918, places=5)
        self.assertAlmostEqual(result["Локсодромия (сфера)"].initial_bearing_deg, 35.161059, places=5)
        self.assertAlmostEqual(result["Геодезическая (WGS 84)"].initial_bearing_deg, 31.903859, places=5)

    def test_equator(self):
        self.assertAlmostEqual(great_circle(0, 0, 0, 10).distance_km, 6371 * 3.141592653589793 / 18, places=6)
        self.assertAlmostEqual(rhumb_line(0, 0, 0, 10).distance_km, 6371 * 3.141592653589793 / 18, places=6)

    def test_same_point_disallowed(self):
        with self.assertRaises(ValueError):
            compare(20, 30, 20, 30)


if __name__ == "__main__":
    unittest.main()
