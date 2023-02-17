from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import KeurigCoordinator
from homeassistant.core import HomeAssistant, callback
from .const import (
    ATTR_POD_BRAND,
    ATTR_POD_IS_FLAVORED,
    ATTR_POD_IS_ICED,
    ATTR_POD_IS_POWDERED,
    ATTR_POD_IS_TEA,
    ATTR_POD_ROAST_TYPE,
    ATTR_POD_VARIETY,
    DOMAIN,
    MANUFACTURER,
)
from homeassistant.components.sensor import SensorEntity


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: KeurigCoordinator = hass.data[DOMAIN][config.entry_id]

    devices = None
    try:
        devices = await coordinator.get_devices()
    except Exception as ex:
        raise ConfigEntryNotReady("Failed to retrieve Keurig devices") from ex

    entities = []
    for brewer in devices:
        await brewer.async_update()
        entities.append(
            KeurigSensorEntity(
                hass=hass,
                name="Pod Status",
                device=brewer,
                coordinator=coordinator,
                device_type="pod_status",
            )
        )
        entities.append(
            KeurigSensorEntity(
                hass=hass,
                name="Brewer Status",
                device=brewer,
                coordinator=coordinator,
                device_type="brewer_status",
            )
        )

    add_entities(entities)


class KeurigSensorEntity(SensorEntity, CoordinatorEntity):
    def __init__(self, hass, name, device, coordinator, device_type):
        self._hass = hass
        self._device = device
        self._coordinator = coordinator
        self._device_type = device_type

        self._attr_name = name
        # self._attr_device_class = device_class
        self._attr_has_entity_name = True

        self._attr_unique_id = device.id + "_" + device_type
        self._attr_icon = "mdi:coffee-maker"

        device.register_callback(self._update_data)

        if self._device_type == "pod_status":
            self._attr_native_value = self.__pod_status_string(self._device.pod_status)
            self._attr_extra_state_attributes = {
                ATTR_POD_BRAND: self._device.pod_brand,
                ATTR_POD_VARIETY: self._device.pod_variety,
                ATTR_POD_ROAST_TYPE: self._device.pod_roast_type,
                ATTR_POD_IS_TEA: self._device.pod_is_tea,
                ATTR_POD_IS_ICED: self._device.pod_is_iced,
                ATTR_POD_IS_FLAVORED: self._device.pod_is_flavored,
                ATTR_POD_IS_POWDERED: self._device.pod_is_powdered,
            }
        elif self._device_type == "brewer_status":
            self._attr_native_value = self.__brewer_status_string(
                self._device.brewer_status, self._device.errors
            )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            manufacturer=MANUFACTURER,
            name=device.name,
            model=device.model,
            sw_version=device.sw_version,
        )

        super().__init__(coordinator)

    async def async_will_remove_from_hass(self) -> None:
        self._device.unregister_callback(self._update_data)

    @callback
    def _update_data(self, args):
        if self._device_type == "pod_status":
            self._attr_native_value = self.__pod_status_string(self._device.pod_status)
            self._attr_extra_state_attributes = {
                ATTR_POD_BRAND: self._device.pod_brand,
                ATTR_POD_VARIETY: self._device.pod_variety,
                ATTR_POD_ROAST_TYPE: self._device.pod_roast_type,
                ATTR_POD_IS_TEA: self._device.pod_is_tea,
                ATTR_POD_IS_ICED: self._device.pod_is_iced,
                ATTR_POD_IS_FLAVORED: self._device.pod_is_flavored,
                ATTR_POD_IS_POWDERED: self._device.pod_is_powdered,
            }
        elif self._device_type == "brewer_status":
            self._attr_native_value = self.__brewer_status_string(
                self._device.brewer_status, self._device.errors
            )
        self.schedule_update_ha_state(False)

    def __pod_status_string(self, value: str):
        if value == "EMPTY":
            return "empty"
        elif value == "PUNCHED":
            return "used"
        elif value == "POD":
            return "present"
        elif value == "BAD_IMAGE":
            return "bad image"
        else:
            return value

    def __brewer_status_string(self, value: str, errors: list):
        if value == "BREW_READY":
            return "ready"
        elif value == "BREW_LOCKED":
            if "ADD_WATER" in errors or "BREW_INSUFFICIENT_WATER" in errors:
                return "no water"
            elif "PM_NOT_CYCLED" in errors:
                return "pod not removed"
            elif "PM_NOT_READY" in errors:
                return "lid open"
            else:
                return errors if errors is not None else value
        elif value == "BREW_CANCELING":
            return "canceling"
        elif value == "BREW_IN_PROGRESS":
            return "brewing"
        elif value == "BREW_SUCCESSFUL":
            return "complete"
        else:
            return value
