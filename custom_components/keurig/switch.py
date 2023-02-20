from typing import Any
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import KeurigCoordinator
from homeassistant.core import HomeAssistant, callback
from .const import DOMAIN, MANUFACTURER
from homeassistant.components.switch import SwitchEntity
from pykeurig.const import STATUS_ON, STATUS_BREWING
from pykeurig.keurigapi import UnauthorizedException


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: KeurigCoordinator = hass.data[DOMAIN][config.entry_id]
    devices = None
    try:
        devices = await coordinator.get_devices()
    except Exception as ex:
        raise ConfigEntryNotReady("Failed to retrieve Keurig devices")

    entities = []
    for brewer in devices:
        await brewer.async_update()
        entities.append(
            KeurigSwitchEntity(
                hass=hass, name="Power", device=brewer, coordinator=coordinator
            )
        )

    add_entities(entities)


class KeurigSwitchEntity(SwitchEntity, CoordinatorEntity):
    def __init__(self, hass, name, device, coordinator):
        self._hass = hass
        self._device = device
        self._coordinator: KeurigCoordinator = coordinator

        self._attr_name = name
        # self._attr_device_class = device_class
        self._attr_has_entity_name = True

        self._attr_unique_id = device.id + "_power"
        self._attr_is_on = (
            self._device.appliance_status == STATUS_ON
            or self._device.appliance_status == STATUS_BREWING
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            manufacturer=MANUFACTURER,
            name=device.name,
            model=device.model,
            sw_version=device.sw_version,
        )

        super().__init__(coordinator)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._device.register_callback(self._update_data))

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            await self._device.power_on()
        except UnauthorizedException:
            await self._coordinator.entry.async_start_reauth(self._hass)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            await self._device.power_off()
        except UnauthorizedException:
            await self._coordinator.entry.async_start_reauth(self._hass)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _update_data(self, args):
        self._attr_is_on = (
            self._device.appliance_status == STATUS_ON
            or self._device.appliance_status == STATUS_BREWING
        )
        self.schedule_update_ha_state(False)
