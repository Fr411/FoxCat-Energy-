from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODES
from .coordinator import FoxCatEnergyCoordinator
from .entity import FoxCatEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: FoxCatEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FoxCatModeSelect(coordinator)])


class FoxCatModeSelect(FoxCatEntity, SelectEntity):
    _attr_options = MODES

    def __init__(self, coordinator: FoxCatEnergyCoordinator) -> None:
        super().__init__(coordinator, "mode_ems", "Mode EMS", "mdi:home-lightning-bolt", "ems")

    @property
    def current_option(self) -> str | None:
        return str(self.coordinator.settings.get("mode"))

    async def async_select_option(self, option: str) -> None:
        if option not in MODES:
            return
        await self.coordinator.async_set_mode(option)
