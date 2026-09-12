from __future__ import annotations

from datetime import time
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AI_TASK,
    CONF_BOILER_BINARY,
    CONF_BOILER_CLIMATE,
    CONF_BOILER_POWER_SENSOR,
    CONF_BOILER_TEMP_SENSOR,
    CONF_DISHWASHER_CYCLE,
    CONF_DISHWASHER_OFF_1,
    CONF_DISHWASHER_OFF_2,
    CONF_DISHWASHER_ON_1,
    CONF_DISHWASHER_ON_2,
    CONF_DISHWASHER_SOCKET,
    CONF_DRYER_CYCLE,
    CONF_DRYER_OFF_1,
    CONF_DRYER_OFF_2,
    CONF_DRYER_ON_1,
    CONF_DRYER_ON_2,
    CONF_DRYER_SOCKET,
    CONF_FORECAST_12H,
    CONF_FORECAST_1H,
    CONF_FORECAST_24H,
    CONF_FORECAST_NEXT_HOUR,
    CONF_FORECAST_NOW,
    CONF_FORECAST_PEAK_TODAY,
    CONF_FORECAST_PEAK_TOMORROW,
    CONF_FORECAST_REMAINING_TODAY,
    CONF_FORECAST_THIS_HOUR,
    CONF_FORECAST_TODAY,
    CONF_FORECAST_TOMORROW,
    CONF_GRID_EXPORT_SENSOR,
    CONF_GRID_IMPORT_SENSOR,
    CONF_GRID_LEGACY_SENSOR,
    CONF_HOUSE_SENSOR,
    CONF_INSTALLATION_NAME,
    CONF_PRICE_AVG_TODAY,
    CONF_PRICE_AVG_TOMORROW,
    CONF_PRICE_CURRENT,
    CONF_PRICE_INJECTION,
    CONF_PRICE_MAX_TODAY,
    CONF_PRICE_MAX_TOMORROW,
    CONF_PRICE_MIN_TODAY,
    CONF_PRICE_MIN_TOMORROW,
    CONF_PRICE_NEXT,
    CONF_PRICE_TOMORROW_AVAILABLE,
    CONF_PRI_L1,
    CONF_PRI_L2,
    CONF_PRI_L3,
    CONF_PRI_L4,
    CONF_PV_SENSOR,
    CONF_TARIFF_HP_END_1,
    CONF_TARIFF_HP_END_2,
    CONF_TARIFF_HP_START_1,
    CONF_TARIFF_HP_START_2,
    CONF_WASHER_CYCLE,
    CONF_WASHER_OFF_1,
    CONF_WASHER_OFF_2,
    CONF_WASHER_ON_1,
    CONF_WASHER_ON_2,
    CONF_WASHER_SOCKET,
    DOMAIN,
)


def _entity(domain: str | list[str], device_class: str | None = None) -> selector.EntitySelector:
    cfg: dict[str, Any] = {"domain": domain}
    if device_class:
        cfg["device_class"] = device_class
    return selector.EntitySelector(selector.EntitySelectorConfig(**cfg))


def _required(key: str, default: str) -> vol.Required:
    return vol.Required(key, default=default)


def _optional(key: str, default: str | None = None) -> vol.Optional:
    return vol.Optional(key, default=default) if default is not None else vol.Optional(key)


def _normalise_value(value: Any) -> Any:
    """Return values that ConfigEntry storage can serialise reliably."""
    if isinstance(value, time):
        return value.isoformat()
    return value


def _normalise_input(user_input: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalise_value(value) for key, value in user_input.items()}


# IMPORTANT: schemas are built lazily.  Home Assistant first imports this module
# to register the ConfigFlow handler.  Building all selectors at import time made
# a single selector/API incompatibility capable of preventing the handler from
# being registered, which surfaced in the UI as "Invalid handler specified".
def _core_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_INSTALLATION_NAME, default="FoxCat Energy"): selector.TextSelector(),
            _required(CONF_PV_SENSOR, "sensor.homefoxcat_load_solaire"): _entity("sensor"),
            _required(CONF_HOUSE_SENSOR, "sensor.consommation_reelle_maison"): _entity("sensor"),
            _required(CONF_GRID_EXPORT_SENSOR, "sensor.restitution_reseau"): _entity("sensor"),
            _required(CONF_GRID_IMPORT_SENSOR, "sensor.consommation_instantanee_0"): _entity("sensor"),
            _optional(CONF_GRID_LEGACY_SENSOR, "sensor.retourne_au_reseau"): _entity("sensor"),
        }
    )


def _boiler_schema() -> vol.Schema:
    return vol.Schema(
        {
            _required(CONF_BOILER_CLIMATE, "climate.buanderie_boiler_chauffe_eau"): _entity("climate"),
            _required(CONF_BOILER_TEMP_SENSOR, "sensor.garage_boiler_sonde_temperature_temperature"): _entity("sensor"),
            _required(CONF_BOILER_POWER_SENSOR, "sensor.boiler_puissance"): _entity("sensor"),
            _required(CONF_BOILER_BINARY, "binary_sensor.boiler"): _entity("binary_sensor"),
        }
    )


def _pri_schema() -> vol.Schema:
    return vol.Schema(
        {
            _required(CONF_PRI_L1, "switch.l1_pri"): _entity("switch"),
            _required(CONF_PRI_L2, "switch.l2_pri"): _entity("switch"),
            _required(CONF_PRI_L3, "switch.l3_pri"): _entity("switch"),
            _required(CONF_PRI_L4, "switch.l4_pri"): _entity("switch"),
        }
    )


def _machines_schema() -> vol.Schema:
    return vol.Schema(
        {
            _optional(CONF_WASHER_SOCKET, "switch.lave_linge_prise_1"): _entity("switch"),
            _optional(CONF_WASHER_CYCLE, "input_boolean.lave_linge_en_cours"): _entity(["binary_sensor", "input_boolean"]),
            vol.Optional(CONF_WASHER_ON_1, default="21:30:00"): selector.TimeSelector(),
            vol.Optional(CONF_WASHER_OFF_1, default="07:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_WASHER_ON_2, default="10:30:00"): selector.TimeSelector(),
            vol.Optional(CONF_WASHER_OFF_2, default="17:00:00"): selector.TimeSelector(),
            _optional(CONF_DRYER_SOCKET, "switch.seche_linge_prise_1"): _entity("switch"),
            _optional(CONF_DRYER_CYCLE, "input_boolean.seche_linge_en_cours"): _entity(["binary_sensor", "input_boolean"]),
            vol.Optional(CONF_DRYER_ON_1, default="21:30:00"): selector.TimeSelector(),
            vol.Optional(CONF_DRYER_OFF_1, default="07:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_DRYER_ON_2, default="10:30:00"): selector.TimeSelector(),
            vol.Optional(CONF_DRYER_OFF_2, default="17:00:00"): selector.TimeSelector(),
            _optional(CONF_DISHWASHER_SOCKET, "switch.lave_vaisselle_prise_1"): _entity("switch"),
            _optional(CONF_DISHWASHER_CYCLE, "input_boolean.lave_vaisselle_en_cours"): _entity(["binary_sensor", "input_boolean"]),
            vol.Optional(CONF_DISHWASHER_ON_1, default="21:30:00"): selector.TimeSelector(),
            vol.Optional(CONF_DISHWASHER_OFF_1, default="07:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_DISHWASHER_ON_2, default="10:30:00"): selector.TimeSelector(),
            vol.Optional(CONF_DISHWASHER_OFF_2, default="17:00:00"): selector.TimeSelector(),
        }
    )


def _pricing_schema() -> vol.Schema:
    return vol.Schema(
        {
            _optional(CONF_PRICE_CURRENT, "sensor.luminus_luminus_dynamic_wallonia_prix_actuel"): _entity("sensor"),
            _optional(CONF_PRICE_NEXT, "sensor.luminus_luminus_dynamic_wallonia_prix_heure_suivante"): _entity("sensor"),
            _optional(CONF_PRICE_INJECTION, "sensor.luminus_luminus_dynamic_wallonia_prix_d_injection"): _entity("sensor"),
            _optional(CONF_PRICE_MIN_TODAY, "sensor.luminus_luminus_dynamic_wallonia_minimum_aujourd_hui"): _entity("sensor"),
            _optional(CONF_PRICE_MAX_TODAY, "sensor.luminus_luminus_dynamic_wallonia_maximum_aujourd_hui"): _entity("sensor"),
            _optional(CONF_PRICE_AVG_TODAY, "sensor.luminus_luminus_dynamic_wallonia_moyenne_aujourd_hui"): _entity("sensor"),
            _optional(CONF_PRICE_MIN_TOMORROW, "sensor.luminus_luminus_dynamic_wallonia_minimum_demain"): _entity("sensor"),
            _optional(CONF_PRICE_MAX_TOMORROW, "sensor.luminus_luminus_dynamic_wallonia_maximum_demain"): _entity("sensor"),
            _optional(CONF_PRICE_AVG_TOMORROW, "sensor.luminus_luminus_dynamic_wallonia_moyenne_demain"): _entity("sensor"),
            _optional(CONF_PRICE_TOMORROW_AVAILABLE, "binary_sensor.luminus_luminus_dynamic_wallonia_prix_de_demain_disponibles"): _entity("binary_sensor"),
            vol.Optional(CONF_TARIFF_HP_START_1, default="07:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_TARIFF_HP_END_1, default="11:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_TARIFF_HP_START_2, default="17:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_TARIFF_HP_END_2, default="22:00:00"): selector.TimeSelector(),
        }
    )


def _solar_schema() -> vol.Schema:
    return vol.Schema(
        {
            _optional(CONF_AI_TASK, "ai_task.google_ai_task"): _entity("ai_task"),
            _optional(CONF_FORECAST_NOW, "sensor.solar_production_forecast_production_d_electricite_estimee_maintenant"): _entity("sensor"),
            _optional(CONF_FORECAST_THIS_HOUR, "sensor.solar_production_forecast_production_d_energie_estimee_cette_heure"): _entity("sensor"),
            _optional(CONF_FORECAST_NEXT_HOUR, "sensor.solar_production_forecast_production_d_energie_estimee_heure_suivante"): _entity("sensor"),
            _optional(CONF_FORECAST_TODAY, "sensor.solar_production_forecast_production_d_energie_estimee_aujourd_hui"): _entity("sensor"),
            _optional(CONF_FORECAST_REMAINING_TODAY, "sensor.solar_production_forecast_production_d_energie_estimee_restante_aujourd_hui"): _entity("sensor"),
            _optional(CONF_FORECAST_1H, "sensor.solar_production_forecast_production_d_energie_estimee_en_1_heure"): _entity("sensor"),
            _optional(CONF_FORECAST_12H, "sensor.solar_production_forecast_production_d_energie_estimee_en_12_heures"): _entity("sensor"),
            _optional(CONF_FORECAST_24H, "sensor.solar_production_forecast_production_d_energie_estimee_en_24_heures"): _entity("sensor"),
            _optional(CONF_FORECAST_PEAK_TODAY, "sensor.solar_production_forecast_heure_de_pointe_de_puissance_la_plus_elevee_aujourd_hui"): _entity("sensor"),
            _optional(CONF_FORECAST_TOMORROW, "sensor.solar_production_forecast_estimation_de_la_production_d_energie_demain"): _entity("sensor"),
            _optional(CONF_FORECAST_PEAK_TOMORROW, "sensor.solar_production_forecast_heure_de_pointe_de_puissance_la_plus_elevee_demain"): _entity("sensor"),
        }
    )


_SCHEMA_BUILDERS = {
    "core": _core_schema,
    "boiler": _boiler_schema,
    "pri": _pri_schema,
    "machines": _machines_schema,
    "pricing": _pricing_schema,
    "solar": _solar_schema,
}


def _schema_with_current(schema: vol.Schema, current: dict[str, Any]) -> vol.Schema:
    fields: dict[Any, Any] = {}
    for marker, validator in schema.schema.items():
        key = marker.schema
        if key in current:
            value = _normalise_value(current[key])
            if isinstance(marker, vol.Required):
                new_marker = vol.Required(key, default=value)
            else:
                new_marker = vol.Optional(key, description={"suggested_value": value})
        else:
            new_marker = marker
        fields[new_marker] = validator
    return vol.Schema(fields)


class FoxCatEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial installation flow for FoxCat Energy."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            self._data.update(_normalise_input(user_input))
            return await self.async_step_boiler()
        return self.async_show_form(step_id="user", data_schema=_core_schema())

    async def async_step_boiler(self, user_input=None):
        if user_input is not None:
            self._data.update(_normalise_input(user_input))
            return await self.async_step_pri()
        return self.async_show_form(step_id="boiler", data_schema=_boiler_schema())

    async def async_step_pri(self, user_input=None):
        if user_input is not None:
            self._data.update(_normalise_input(user_input))
            return await self.async_step_machines()
        return self.async_show_form(step_id="pri", data_schema=_pri_schema())

    async def async_step_machines(self, user_input=None):
        if user_input is not None:
            self._data.update(_normalise_input(user_input))
            return await self.async_step_pricing()
        return self.async_show_form(step_id="machines", data_schema=_machines_schema())

    async def async_step_pricing(self, user_input=None):
        if user_input is not None:
            self._data.update(_normalise_input(user_input))
            return await self.async_step_solar()
        return self.async_show_form(step_id="pricing", data_schema=_pricing_schema())

    async def async_step_solar(self, user_input=None):
        if user_input is not None:
            self._data.update(_normalise_input(user_input))
            title = str(self._data.get(CONF_INSTALLATION_NAME, "FoxCat Energy"))
            await self.async_set_unique_id("foxcat_energy_main")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=title, data=self._data)
        return self.async_show_form(step_id="solar", data_schema=_solar_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Return the transactional options flow.

        Home Assistant attaches config_entry to the OptionsFlow instance.
        """
        return FoxCatEnergyOptionsFlow()


class FoxCatEnergyOptionsFlow(config_entries.OptionsFlow):
    """Transactional options flow.

    No ConfigEntry mutation occurs while the menu is open.  Changes are kept in
    memory and committed once with async_create_entry() at "finish".  The
    ConfigEntry update listener can therefore reload FoxCat only after the flow
    is complete instead of destroying an active flow.
    """

    def __init__(self) -> None:
        super().__init__()
        self._pending_options: dict[str, Any] | None = None

    def _ensure_pending(self) -> dict[str, Any]:
        if self._pending_options is None:
            self._pending_options = dict(self.config_entry.options)
        return self._pending_options

    def _effective(self) -> dict[str, Any]:
        data = dict(self.config_entry.data)
        data.update(self._ensure_pending())
        return data

    async def async_step_init(self, user_input=None):
        self._ensure_pending()
        return self.async_show_menu(
            step_id="init",
            menu_options=["core", "boiler", "pri", "machines", "pricing", "solar", "finish"],
        )

    async def _section(self, step_id: str, user_input):
        if user_input is not None:
            self._ensure_pending().update(_normalise_input(user_input))
            return await self.async_step_init()
        schema = _SCHEMA_BUILDERS[step_id]()
        return self.async_show_form(
            step_id=step_id,
            data_schema=_schema_with_current(schema, self._effective()),
        )

    async def async_step_core(self, user_input=None):
        return await self._section("core", user_input)

    async def async_step_boiler(self, user_input=None):
        return await self._section("boiler", user_input)

    async def async_step_pri(self, user_input=None):
        return await self._section("pri", user_input)

    async def async_step_machines(self, user_input=None):
        return await self._section("machines", user_input)

    async def async_step_pricing(self, user_input=None):
        return await self._section("pricing", user_input)

    async def async_step_solar(self, user_input=None):
        return await self._section("solar", user_input)

    async def async_step_finish(self, user_input=None):
        return self.async_create_entry(title="", data=self._ensure_pending())
