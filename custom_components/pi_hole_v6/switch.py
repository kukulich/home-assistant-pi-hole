"""Support for turning on and off Pi-hole system."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PiHoleV6ConfigEntry
from .const import SERVICE_DISABLE, SERVICE_DISABLE_ATTR_DURATION, SERVICE_ENABLE
from .entity import PiHoleV6Entity
from .exceptions import (
    BadGatewayException,
    BadRequestException,
    ForbiddenException,
    GatewayTimeoutException,
    NotFoundException,
    RequestFailedException,
    ServerErrorException,
    ServiceUnavailableException,
    TooManyRequestsException,
    UnauthorizedException,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PiHoleV6ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Pi-hole V6 switch."""
    name = entry.data[CONF_NAME]
    hole_data = entry.runtime_data
    switches = [
        PiHoleV6Switch(
            hole_data.api,
            hole_data.coordinator,
            name,
            entry.entry_id,
        )
    ]
    async_add_entities(switches, True)

    # register service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_DISABLE,
        {
            vol.Required(SERVICE_DISABLE_ATTR_DURATION): vol.All(
                cv.time_period_str, cv.positive_timedelta
            ),
        },
        "async_service_disable",
    )
    platform.async_register_entity_service(
        SERVICE_ENABLE,
        {},
        "async_service_enable",
    )


class PiHoleV6Switch(PiHoleV6Entity, SwitchEntity):
    """Representation of a Pi-hole V6 switch."""

    _attr_icon = "mdi:pi-hole"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return f"{self._server_unique_id}/Switch"

    @property
    def is_on(self) -> bool:
        """Return if the service is on."""
        return bool(self.api.cache_blocking.get("blocking", None) == "enabled")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the service."""
        await self.async_turn(action="enable")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the service."""
        await self.async_turn(action="disable")

    async def async_turn(self, action: str, duration: Any = None) -> None:
        """Turn on/off the service."""

        try:
            if action == "enable":
                await self.api.call_blocking_enabled()

            if action == "disable":
                await self.api.call_blocking_disabled(duration)

            await self.async_update()
            self.schedule_update_ha_state(force_refresh=True)

        except (
            BadRequestException,
            UnauthorizedException,
            RequestFailedException,
            ForbiddenException,
            NotFoundException,
            TooManyRequestsException,
            ServerErrorException,
            BadGatewayException,
            ServiceUnavailableException,
            GatewayTimeoutException,
        ) as err:
            _LOGGER.error("Unable to %s Pi-hole V6: %s", action, err)

    async def async_service_disable(self, duration: Any = None) -> None:
        """..."""

        duration_seconds = duration.total_seconds()

        _LOGGER.debug(
            "Disabling Pi-hole '%s' for %d seconds",
            self.name,
            duration_seconds,
        )

        await self.async_turn(action="disable", duration=duration_seconds)

    async def async_service_enable(self) -> None:
        """..."""

        _LOGGER.debug("Enabling Pi-hole '%s'", self.name)
        await self.async_turn(action="enable")
