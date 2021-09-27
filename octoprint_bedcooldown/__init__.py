# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.util
from octoprint.events import Events


class BedCooldown(
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
):

    _bedcooldown_timer = None

    ##~~ EventHandlerPlugin mixin

    def on_event(self, event, payload):
        if not self._settings.get_boolean(["enabled"]):
            return

        if event == Events.PRINT_STARTED:
            self._logger.info(
                "Bed cooldown will be triggered when time left is <= {}s and completion is >= {}%".format(
                    self._settings.get_int(["time_left"]),
                    self._settings.get_int(["completion"]),
                )
            )
            self._bedcooldown_timer = octoprint.util.RepeatedTimer(
                30, self._bedcooldown_timer_triggered
            )
            self._bedcooldown_timer.start()
        elif event in (Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED):
            if self._bedcooldown_timer is not None:
                self._bedcooldown_timer.cancel()
                self._bedcooldown_timer = None

    def _bedcooldown_timer_triggered(self):
        if not self._printer.is_printing():
            return
        current_data = self._printer.get_current_data()
        if (
            current_data["progress"]["printTimeLeft"]
            <= self._settings.get_int(["time_left"])
        ) and (
            current_data["progress"]["completion"]
            >= self._settings.get_int(["completion"])
        ):
            self._logger.info("Bed cooldown triggered, turning off bed heater")
            self._printer.commands("M140 S0")
            self._bedcooldown_timer.cancel()
            self._bedcooldown_timer = None

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(enabled=True, time_left=300, completion=90)

    ##~~ TemplatePlugin mixin

    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "bedcooldown": {
                "displayName": "Bed Cooldown",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "rfinnie",
                "repo": "OctoPrint-BedCooldown",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/rfinnie/OctoPrint-BedCooldown/archive/v{target_version}.zip",
            }
        }


__plugin_name__ = "Bed Cooldown"
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = BedCooldown()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
