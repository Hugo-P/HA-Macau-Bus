from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import HomeAssistantView

from .const import DOMAIN

PLATFORMS = ["sensor"]
CARD_URL = f"/{DOMAIN}/macau-bus-card.js"
_JS_CONTENT = None


class MacauBusCardView(HomeAssistantView):
    url = CARD_URL
    name = f"{DOMAIN}_card"
    requires_auth = False

    async def get(self, request):
        global _JS_CONTENT
        if _JS_CONTENT is None:
            from pathlib import Path
            _JS_CONTENT = (Path(__file__).parent / "www" / "macau-bus-card.js").read_text(encoding="utf-8")
        return await self._serve_file()

    async def _serve_file(self):
        from aiohttp import web
        return web.Response(text=_JS_CONTENT, content_type="application/javascript")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.http.register_view(MacauBusCardView())
    add_extra_js_url(hass, CARD_URL)
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(entry.entry_id, None)
    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
