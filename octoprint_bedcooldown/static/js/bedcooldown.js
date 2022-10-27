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
