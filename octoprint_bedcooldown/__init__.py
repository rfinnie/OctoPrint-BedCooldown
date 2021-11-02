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

    # EventHandlerPlugin mixin

    def on_event(self, event, payload):
        if event not in (
            Events.PRINT_STARTED,
            Events.PRINT_DONE,
            Events.PRINT_FAILED,
            Events.PRINT_CANCELLED,
        ):
            return
        self._logger.debug("Handling {event} event".format(event=event))

        if event == Events.PRINT_STARTED:
            self._logger.info(
                "Bed cooldown trigger is configured for when time left is <= {time_left}s "
                "and completion is >= {completion:0.02f}%".format(
                    time_left=self._settings.get_int(["time_left"]),
                    completion=self._settings.get_int(["completion"]),
                )
            )
            if not self._settings.get_boolean(["enabled"]):
                self._logger.info("However, plugin is not currently enabled")

            self._logger.debug("Scheduling RepeatedTimer for 30 seconds")
            self._bedcooldown_timer = octoprint.util.RepeatedTimer(
                30, self._bedcooldown_timer_triggered
            )
            self._bedcooldown_timer.start()
        elif event in (Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED):
            if self._bedcooldown_timer is not None:
                self._logger.debug(
                    "Print ended via {event} event, cancelling timer".format(
                        event=event
                    )
                )
                self._bedcooldown_timer.cancel()
                self._bedcooldown_timer = None

    def _bedcooldown_timer_triggered(self):
        if not self._settings.get_boolean(["enabled"]):
            self._logger.debug("Plugin is not enabled")
            return

        if not self._printer.is_printing():
            self._logger.warning(
                "_bedcooldown_timer_triggered triggered but not printing? This shouldn't happen."
            )
            return
        current_data = self._printer.get_current_data()
        time_elapsed = current_data["progress"]["printTime"]
        time_left = current_data["progress"]["printTimeLeft"]
        time_left_origin = current_data["progress"]["printTimeLeftOrigin"]
        completion_time = (float(time_elapsed) / (time_elapsed + time_left)) * 100.0
        completion_gcode = current_data["progress"]["completion"]
        settings_time_left = self._settings.get_int(["time_left"])
        settings_completion = self._settings.get_int(["completion"])
        settings_completion_use_gcode = self._settings.get_boolean(
            ["completion_use_gcode"]
        )
        if settings_completion_use_gcode:
            completion = completion_gcode
            completion_type = "gcode"
        else:
            completion = completion_time
            completion_type = "time"
        self._logger.debug(
            (
                "Time: {time_elapsed}s elapsed, {time_left}s left (via {time_left_origin}). "
                "Completion: {completion_time:0.02f}% time, "
                "{completion_gcode:0.02f}% gcode (using {completion_type}). "
                "Threshold: {time_left}s/{settings_time_left}s, "
                "{completion:0.02f}%/{settings_completion:0.02f}%".format(
                    time_elapsed=time_elapsed,
                    time_left=time_left,
                    time_left_origin=time_left_origin,
                    completion_time=completion_time,
                    completion_gcode=completion_gcode,
                    completion_type=completion_type,
                    settings_time_left=settings_time_left,
                    completion=completion,
                    settings_completion=settings_completion,
                )
            )
        )
        if (time_left <= settings_time_left) and (completion >= settings_completion):
            self._logger.info(
                (
                    "Bed cooldown triggered (<= {settings_time_left}s, "
                    ">= {settings_completion:0.02f}%), turning off bed heater"
                ).format(
                    settings_time_left=settings_time_left,
                    settings_completion=settings_completion,
                )
            )
            self._printer.commands("M140 S0")
            self._bedcooldown_timer.cancel()
            self._bedcooldown_timer = None

            self._event_bus.fire(
                Events.PLUGIN_BEDCOOLDOWN_COOLDOWN_TRIGGERED,
                {
                    "settings_completion": settings_completion,
                    "settings_time_left": settings_time_left,
                    "completion": completion,
                    "time_left": time_left,
                },
            )

    # SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            enabled=True, time_left=300, completion=90, completion_use_gcode=False
        )

    # TemplatePlugin mixin

    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    # Softwareupdate hook

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
                "pip": "https://github.com/rfinnie/OctoPrint-BedCooldown/archive/{target_version}.zip",
            }
        }

    # Events hook

    def register_custom_events(self, *args, **kwargs):
        return ["cooldown_triggered"]


__plugin_name__ = "Bed Cooldown"
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = BedCooldown()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events,
    }
