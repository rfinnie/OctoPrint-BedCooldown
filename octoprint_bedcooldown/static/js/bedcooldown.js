/*
SPDX-PackageName: Octoprint-BedCooldown
SPDX-PackageSupplier: Ryan Finnie <ryan@finnie.org>
SPDX-PackageDownloadLocation: https://codeberg.org/rfinnie/Octoprint-BedCooldown
SPDX-FileCopyrightText: © 2021 Ryan Finnie <ryan@finnie.org>
SPDX-License-Identifier: MPL-2.0
*/
$(function() {
    function BedCooldownViewModel(parameters) {
        // Dummy translation requests for dynamic strings supplied by the backend
        // noinspection BadExpressionStatementJS
        [
            // mark labels
            gettext("Cooldown")
        ];
    };

    OCTOPRINT_VIEWMODELS.push({
        construct: BedCooldownViewModel,
        dependencies: ["temperatureViewModel"],
        elements: []
    });
});
