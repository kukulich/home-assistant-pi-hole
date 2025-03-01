"""The pi_hole_v6 component."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_URL, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import API as PiholeAPI
from .const import DOMAIN, MIN_TIME_BETWEEN_UPDATES

_LOGGER = logging.getLogger(__name__)


PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    # Platform.UPDATE,
]

type PiHoleV6ConfigEntry = ConfigEntry[PiHoleV6Data]


@dataclass
class PiHoleV6Data:
    """Runtime data definition."""

    api: PiholeAPI
    coordinator: DataUpdateCoordinator[None]


async def async_setup_entry(hass: HomeAssistant, entry: PiHoleV6ConfigEntry) -> bool:
    """Set up Pi-hole V6 entry."""
    password = entry.data.get(CONF_PASSWORD, "")
    name = entry.data[CONF_NAME]
    url = entry.data[CONF_URL]

    _LOGGER.debug("Setting up %s integration with host %s", DOMAIN, url)

    name_to_key = {
        "Core Update Available": "core_update_available",
        "Web Update Available": "web_update_available",
        "FTL Update Available": "ftl_update_available",
        "Status": "status",
        "Ads Blocked Today": "ads_blocked_today",
        "Ads Percentage Blocked Today": "ads_percentage_today",
        "Seen Clients": "clients_ever_seen",
        "DNS Queries Today": "dns_queries_today",
        "Domains Blocked": "domains_being_blocked",
        "DNS Queries Cached": "queries_cached",
        "DNS Queries Forwarded": "queries_forwarded",
        "DNS Unique Clients": "unique_clients",
        "DNS Unique Domains": "unique_domains",
    }

    @callback
    def update_unique_id(
        entity_entry: er.RegistryEntry,
    ) -> dict[str, str] | None:
        """Update unique ID of entity entry."""
        unique_id_parts = entity_entry.unique_id.split("/")
        if len(unique_id_parts) == 2 and unique_id_parts[1] in name_to_key:
            name = unique_id_parts[1]
            new_unique_id = entity_entry.unique_id.replace(name, name_to_key[name])
            _LOGGER.debug("Migrate %s to %s", entity_entry.unique_id, new_unique_id)
            return {"new_unique_id": new_unique_id}

        return None

    await er.async_migrate_entries(hass, entry.entry_id, update_unique_id)

    session = async_get_clientsession(hass, False)
    api_client = PiholeAPI(
        session=session,
        url=url,
        password=password,
        logger=_LOGGER,
    )

    async def async_update_data() -> None:
        """Fetch data from API endpoint."""

        if not isinstance(await api_client.call_summary(), dict):
            raise ConfigEntryAuthFailed

        if not isinstance(await api_client.call_blocking_status(), dict):
            raise ConfigEntryAuthFailed

        if not isinstance(await api_client.call_padd(), dict):
            raise ConfigEntryAuthFailed

        if not isinstance(await api_client.call_get_groups(), dict):
            raise ConfigEntryAuthFailed

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
        name=name,
        update_method=async_update_data,
        update_interval=MIN_TIME_BETWEEN_UPDATES,
    )

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = PiHoleV6Data(api_client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Pi-hole entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
