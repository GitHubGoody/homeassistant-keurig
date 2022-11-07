"""The Keurig Connect integration."""
from __future__ import annotations
import asyncio
from .helpers import get_brewers_for_service

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_AREA_ID,
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    ATTR_ID,
    ATTR_NAME,
    ATTR_TEMPERATURE,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pykeurig.keurigapi import KeurigApi, UnauthorizedException

from .const import (
    ATTR_SIZE,
    DOMAIN,
    SERVICE_ADD_FAVORITE,
    SERVICE_BREW_FAVORITE,
    SERVICE_BREW_HOT_WATER,
    SERVICE_BREW_HOT,
    ATTR_INTENSITY,
    SERVICE_BREW_ICED,
    SERVICE_BREW_RECOMMENDATION,
    SERVICE_CANCEL_BREW,
    SERVICE_DELETE_FAVORITE,
    SERVICE_UPDATE_FAVORITE,
)
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Keurig Connect from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    client = KeurigApi()
    await client.login(entry.data.get(CONF_USERNAME), entry.data.get(CONF_PASSWORD))

    coordinator = KeurigCoordinator(hass, client, entry)

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()

    async def handle_brew_hot_water(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        size = call.data.get(ATTR_SIZE)
        temperature = call.data.get(ATTR_TEMPERATURE)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.hot_water(int(size), int(temperature))
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(DOMAIN, SERVICE_BREW_HOT_WATER, handle_brew_hot_water)

    async def handle_brew_hot(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        size = call.data.get(ATTR_SIZE)
        temperature = call.data.get(ATTR_TEMPERATURE)
        intensity = call.data.get(ATTR_INTENSITY)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.brew_hot(int(size), int(temperature), int(intensity))
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(DOMAIN, SERVICE_BREW_HOT, handle_brew_hot)

    async def handle_brew_iced(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.brew_iced()
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(DOMAIN, SERVICE_BREW_ICED, handle_brew_iced)

    async def handle_brew_recommendation(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        size = call.data.get(ATTR_SIZE)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.brew_recommendation(int(size))
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(
        DOMAIN, SERVICE_BREW_RECOMMENDATION, handle_brew_recommendation
    )

    async def handle_brew_favorite(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        favorite_id = call.data.get(ATTR_ID)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.brew_favorite(favorite_id)
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(DOMAIN, SERVICE_BREW_FAVORITE, handle_brew_favorite)

    async def handle_cancel_brew(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.cancel_brew()
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(DOMAIN, SERVICE_CANCEL_BREW, handle_cancel_brew)

    async def handle_add_favorite(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        name = call.data.get(ATTR_NAME)
        size = call.data.get(ATTR_SIZE)
        temperature = call.data.get(ATTR_TEMPERATURE)
        intensity = call.data.get(ATTR_INTENSITY)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.add_favorite(
                    name, int(size), int(temperature), int(intensity)
                )
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(DOMAIN, SERVICE_ADD_FAVORITE, handle_add_favorite)

    async def handle_update_favorite(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        favorite_id = call.data.get(ATTR_ID)
        name = call.data.get(ATTR_NAME)
        size = call.data.get(ATTR_SIZE)
        temperature = call.data.get(ATTR_TEMPERATURE)
        intensity = call.data.get(ATTR_INTENSITY)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.update_favorite(
                    favorite_id, name, int(size), int(temperature), int(intensity)
                )
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_FAVORITE, handle_update_favorite
    )

    async def handle_delete_favorite(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        favorite_id = call.data.get(ATTR_ID)
        matched_devices = get_brewers_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                (dev for dev in await coordinator.get_devices() if dev.id == device_id)
            )
            try:
                await device.delete_favorite(favorite_id)
            except UnauthorizedException:
                await entry.async_start_reauth(hass)

    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_FAVORITE, handle_delete_favorite
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class KeurigCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self, hass: HomeAssistant, api: KeurigApi, entry: ConfigEntry, devices=None
    ):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Keurig",
        )
        self.api = api
        self.hass: HomeAssistant = hass
        self.entry = entry
        self._devices = None
        self._device_lock = asyncio.Lock()

    async def get_devices(self):
        async with self._device_lock:
            if self._devices is None:
                try:
                    self._devices = await self.api.async_get_devices()
                except UnauthorizedException:
                    await self.entry.async_start_reauth(self.hass)
            return self._devices

    async def _async_update_data(self):
        await self.hass.async_add_executor_job(self.api.connect)
