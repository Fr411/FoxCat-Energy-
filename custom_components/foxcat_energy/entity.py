from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import FoxCatEnergyCoordinator


class FoxCatEntity(CoordinatorEntity[FoxCatEnergyCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FoxCatEnergyCoordinator, key: str, name: str, icon: str | None = None, device: str = "ems") -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_icon = icon
        self._device = device

    @property
    def device_info(self) -> DeviceInfo:
        names = {
            "ems": "FoxCat Energy – EMS",
            "boiler": "FoxCat Energy – Boiler",
            "pri": "FoxCat Energy – PRI SolarEdge",
            "machines": "FoxCat Energy – Machines",
            "solar": "FoxCat Energy – EMS 2",
            "pricing": "FoxCat Energy – Tarification",
            "hardware": "FoxCat Energy – Matériel installé",
        }
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.entry.entry_id}:{self._device}")},
            name=names.get(self._device, "FoxCat Energy"),
            manufacturer="FoxCat Energy",
            model="EMS Python",
            sw_version=VERSION,
            via_device=(DOMAIN, f"{self.coordinator.entry.entry_id}:ems") if self._device != "ems" else None,
        )
