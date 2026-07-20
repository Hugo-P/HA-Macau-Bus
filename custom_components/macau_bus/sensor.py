import logging
from datetime import timedelta

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, DEFAULT_RADIUS, DEFAULT_SCAN_INTERVAL
from .api import build_dashboard

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = MacauBusCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([MacauBusSensor(coordinator, entry)])


def _get_entry_option(entry, key, default=None):
    return entry.options.get(key, entry.data.get(key, default))


class MacauBusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self._entry = entry
        self._device_tracker = _get_entry_option(entry, "device_tracker")
        self._radius = _get_entry_option(entry, "radius", DEFAULT_RADIUS)
        update_interval = timedelta(seconds=_get_entry_option(entry, "scan_interval", DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        state = self.hass.states.get(self._device_tracker)
        if not state or not state.attributes.get("latitude"):
            raise UpdateFailed(f"裝置 {self._device_tracker} 無 GPS 資料")
        lat = str(state.attributes["latitude"])
        lon = str(state.attributes["longitude"])
        route_filter = _get_entry_option(self._entry, "routes", "")

        try:
            result = await self.hass.async_add_executor_job(
                build_dashboard, lat, lon, self._radius, route_filter
            )
            return result
        except Exception as err:
            raise UpdateFailed(f"Error fetching Macau bus data: {err}")


class MacauBusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Macau Bus"
        self._attr_unique_id = f"{entry.entry_id}_macau_bus"
        self._attr_icon = "mdi:bus"

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return STATE_UNKNOWN
        if "error" in data:
            return data["error"]
        routes = data.get("routes", [])
        return f"{len(routes)} 條路線" if routes else "未有資料"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        state = self.hass.states.get(self.coordinator._device_tracker)
        user_lat = state.attributes["latitude"] if state and state.attributes.get("latitude") else None
        user_lon = state.attributes["longitude"] if state and state.attributes.get("longitude") else None
        return {
            "nearbyStops": data.get("nearbyStops", []),
            "routes": data.get("routes", []),
            "totalRoutes": data.get("totalRoutes", 0),
            "checkedRoutes": data.get("checkedRoutes", 0),
            "timestamp": data.get("timestamp", ""),
            "user_lat": user_lat,
            "user_lon": user_lon,
        }
