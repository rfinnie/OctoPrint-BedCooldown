import unittest

import octoprint_bedcooldown


class TestBedCooldown(unittest.TestCase):
    def test_basics(self):
        self.assertEqual(octoprint_bedcooldown.__plugin_name__, "Bed Cooldown")
