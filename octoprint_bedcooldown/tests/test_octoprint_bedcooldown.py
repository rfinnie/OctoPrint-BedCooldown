# SPDX-PackageName: Octoprint-BedCooldown
# SPDX-PackageSupplier: Ryan Finnie <ryan@finnie.org>
# SPDX-PackageDownloadLocation: https://forge.colobox.com/rfinnie/Octoprint-BedCooldown
# SPDX-FileCopyrightText: © 2021 Ryan Finnie <ryan@finnie.org>
# SPDX-License-Identifier: MPL-2.0
import unittest

import octoprint_bedcooldown


class TestBedCooldown(unittest.TestCase):
    def test_basics(self):
        self.assertEqual(octoprint_bedcooldown.__plugin_name__, "Bed Cooldown")
