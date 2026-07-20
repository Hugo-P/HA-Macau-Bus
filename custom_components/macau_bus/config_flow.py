import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, DEFAULT_RADIUS, DEFAULT_SCAN_INTERVAL, CONF_ROUTES

_LOGGER = logging.getLogger(__name__)


class MacauBusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="澳門巴士 Macau Bus", data=user_input)

        device_trackers = self._get_device_trackers()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("device_tracker"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=device_trackers,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(CONF_ROUTES, default=""): str,
                vol.Optional("radius", default=DEFAULT_RADIUS): int,
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MacauBusOptionsFlow()

    @callback
    def _get_device_trackers(self):
        states = self.hass.states.async_all("device_tracker")
        return [s.entity_id for s in states if s.entity_id]


class MacauBusOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        entry = self.config_entry
        data = {**entry.data, **entry.options}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        device_trackers = [
            s.entity_id
            for s in self.hass.states.async_all("device_tracker")
            if s.entity_id
        ]
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("device_tracker", default=data.get("device_tracker", "")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=device_trackers,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(CONF_ROUTES, default=data.get(CONF_ROUTES, "")): str,
                vol.Optional("radius", default=data.get("radius", DEFAULT_RADIUS)): int,
                vol.Optional("scan_interval", default=data.get("scan_interval", DEFAULT_SCAN_INTERVAL)): int,
            }),
        )
