# SPDX-PackageSummary: OctoPrint-BedCooldown
# SPDX-FileCopyrightText: Copyright (C) 2021-2022 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0

from __future__ import absolute_import

from datetime import timedelta
import types

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

    def _get_plugin_settings(self):
        return types.SimpleNamespace(
            enabled=self._settings.get_boolean(["enabled"]),
            temperature=self._settings.get_int(["temperature"]),
            time_elapsed=timedelta(seconds=self._settings.get_int(["time_elapsed"])),
            time_left=timedelta(seconds=self._settings.get_int(["time_left"])),
            completion=(self._settings.get_int(["completion"]) / 100.0),
            completion_use_gcode=self._settings.get_boolean(["completion_use_gcode"]),
        )

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

        settings = self._get_plugin_settings()
        if event == Events.PRINT_STARTED:
            self._logger.info(
                "Bed cooldown trigger to {settings_temperature}C is configured for when "
                "time elapsed is >= {settings_time_elapsed}, time left is <= {settings_time_left}, "
                "and completion is >= {settings_completion:0.02%}".format(
                    settings_temperature=settings.temperature,
                    settings_time_elapsed=settings.time_elapsed,
                    settings_time_left=settings.time_left,
                    settings_completion=settings.completion,
                )
            )
            if not settings.enabled:
                self._logger.info("However, plugin is not currently enabled")

            self._logger.debug("Scheduling RepeatedTimer for 30 seconds")
            self._bedcooldown_timer = octoprint.util.RepeatedTimer(30, self._bedcooldown_timer_triggered_wrapper)
            self._bedcooldown_timer.start()
        elif event in (Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED):
            if self._bedcooldown_timer is not None:
                self._logger.debug("Print ended via {event} event, cancelling timer".format(event=event))
                self._bedcooldown_timer.cancel()
                self._bedcooldown_timer = None

    def _bedcooldown_timer_triggered_wrapper(self):
        try:
            return self._bedcooldown_timer_triggered()
        except Exception:
            self._logger.exception("Uncaught exception in recurring trigger")

    def _bedcooldown_timer_triggered(self):
        self._logger.debug("Recurring trigger")
        settings = self._get_plugin_settings()
        if not settings.enabled:
            self._logger.debug("Plugin is not enabled")
            return

        if not self._printer.is_printing():
            self._logger.warning("_bedcooldown_timer_triggered triggered but not printing? This shouldn't happen.")
            return
        current_data = self._printer.get_current_data()
        progress = current_data.get("progress", {})
        progress_keys = (
            "printTime",
            "printTimeLeft",
            "printTimeLeftOrigin",
            "completion",
        )
        missing_keys = [k for k in progress_keys if k not in progress]
        if missing_keys:
            self._logger.debug("Missing progress keys, ignoring this round: {}".format(missing_keys))
            return
        missing_values = [k for k in progress_keys if progress[k] is None]
        if missing_values:
            self._logger.debug("Missing progress values, ignoring this round: {}".format(missing_values))
            return
        time_elapsed = timedelta(seconds=progress["printTime"])
        time_left = timedelta(seconds=progress["printTimeLeft"])
        time_left_origin = progress["printTimeLeftOrigin"]
        completion_time = time_elapsed / (time_elapsed + time_left)
        completion_gcode = progress["completion"] / 100.0
        if settings.completion_use_gcode:
            completion = completion_gcode
            completion_type = "gcode"
        else:
            completion = completion_time
            completion_type = "time"
        self._logger.debug(
            (
                "Time: {time_elapsed} elapsed, {time_left} left (via {time_left_origin}). "
                "Completion: {completion_time:0.02%} time, "
                "{completion_gcode:0.02%} gcode (using {completion_type}). "
                "Threshold: {time_elapsed}/{settings_time_elapsed} elapsed, "
                "{time_left}/{settings_time_left} left, "
                "{completion:0.02%}/{settings_completion:0.02%}".format(
                    time_elapsed=time_elapsed,
                    time_left=time_left,
                    time_left_origin=time_left_origin,
                    completion_time=completion_time,
                    completion_gcode=completion_gcode,
                    completion_type=completion_type,
                    settings_time_elapsed=settings.time_elapsed,
                    settings_time_left=settings.time_left,
                    completion=completion,
                    settings_completion=settings.completion,
                )
            )
        )
        if (time_elapsed >= settings.time_elapsed) and (time_left <= settings.time_left) and (completion >= settings.completion):
            self._logger.info(
                (
                    "Bed cooldown triggered (>= {settings_time_elapsed} elapsed, "
                    "<= {settings_time_left} left, "
                    ">= {settings_completion:0.02%}), setting bed to {settings_temperature}C"
                ).format(
                    settings_time_elapsed=settings.time_elapsed,
                    settings_time_left=settings.time_left,
                    settings_completion=settings.completion,
                    settings_temperature=settings.temperature,
                )
            )
            self._printer.commands("M140 S{settings_temperature:.0f}".format(settings_temperature=settings.temperature))
            self._bedcooldown_timer.cancel()
            self._bedcooldown_timer = None

            self._event_bus.fire(
                Events.PLUGIN_BEDCOOLDOWN_COOLDOWN_TRIGGERED,
                {
                    "settings": settings,
                    "completion": completion,
                    "time_elapsed": time_elapsed,
                    "time_left": time_left,
                },
            )

            # Extensible chart marking support added in OctoPrint 1.9.0
            if hasattr(Events, "CHART_MARKED"):
                # This marking is styled by bedcooldown.css and translatable via
                # dummy requests in bedcooldown.js
                self._event_bus.fire(
                    Events.CHART_MARKED,
                    {
                        "type": "bedcooldown_cooldown",
                        "label": "Cooldown",
                    },
                )

    # SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            enabled=True,
            time_elapsed=0,
            time_left=300,
            completion=90,
            completion_use_gcode=False,
            temperature=0,
        )

    # TemplatePlugin mixin

    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    # AssetPlugin mixin

    def get_assets(self):
        return dict(
            js=["js/bedcooldown.js"],
            css=["css/bedcooldown.css"],
        )

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
__plugin_pythoncompat__ = ">=3,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = BedCooldown()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events,
    }
