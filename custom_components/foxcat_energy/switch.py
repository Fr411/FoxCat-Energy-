from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SWITCH_DEFINITIONS
from .coordinator import FoxCatEnergyCoordinator
from .entity import FoxCatEntity


def _device_for(key: str) -> str:
    if key.startswith("boiler") or key == "agressivite_ecs":
        return "boiler"
    if key.startswith("pri"):
        return "pri"
    if key in {"washer_enabled", "dryer_enabled", "dishwasher_enabled"}:
        return "machines"
    if key == "solar_advisor_enabled":
        return "solar"
    return "ems"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: FoxCatEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FoxCatSettingSwitch(coordinator, key, name, icon) for key, (name, icon) in SWITCH_DEFINITIONS.items()])


class FoxCatSettingSwitch(FoxCatEntity, SwitchEntity):
    def __init__(self, coordinator: FoxCatEnergyCoordinator, key: str, name: str, icon: str) -> None:
        super().__init__(coordinator, key, name, icon, _device_for(key))

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.settings.get(self._key, False))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_setting(self._key, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_setting(self._key, False)
