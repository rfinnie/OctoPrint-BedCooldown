# OctoPrint-BedCooldown

*Turns off the bed heater toward the end of a print*

For filaments such as PLA, many printers have more than enough stored thermal mass in the bed to keep bed adhesion throughout the print.
Therefore, you may want to turn off the bed heater automatically before the end of a print, saving cooldown time.

The bed heater will be turned off during a print, when both conditions are met:

  * The print time left is below the configured threshold (default 300 seconds / 5 minutes)
  * The print completion percentage is above the configured threshold (default 90%)

This should cover both long and short prints; you wouldn't want the bed to turn off 90% into a 20 hour print, or 5 minutes before the end of a 10 minute total print.

Be sure to monitor your print, as turning off the bed heater could cause the print to come loose prior to completion.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/rfinnie/OctoPrint-BedCooldown/archive/main.zip

## Configuration

You may configure this plugin through OctoPrint's UI.
It may be selectively disabled, and the time left and completion thresholds may be adjusted.
