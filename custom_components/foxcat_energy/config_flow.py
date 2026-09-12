from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import *


def entity(domain: str | list[str], device_class: str | None = None) -> selector.EntitySelector:
    cfg: dict[str, Any] = {"domain": domain}
    if device_class:
        cfg["device_class"] = device_class
    return selector.EntitySelector(selector.EntitySelectorConfig(**cfg))


def _required(key: str, default: str) -> vol.Required:
    return vol.Required(key, default=default)


def _optional(key: str, default: str | None = None) -> vol.Optional:
    return vol.Optional(key, default=default) if default is not None else vol.Optional(key)


CORE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INSTALLATION_NAME, default="FoxCat Energy"): selector.TextSelector(),
        _required(CONF_PV_SENSOR, "sensor.homefoxcat_load_solaire"): entity("sensor"),
        _required(CONF_HOUSE_SENSOR, "sensor.consommation_reelle_maison"): entity("sensor"),
        _required(CONF_GRID_EXPORT_SENSOR, "sensor.restitution_reseau"): entity("sensor"),
        _required(CONF_GRID_IMPORT_SENSOR, "sensor.consommation_instantanee_0"): entity("sensor"),
        _optional(CONF_GRID_LEGACY_SENSOR, "sensor.retourne_au_reseau"): entity("sensor"),
    }
)

BOILER_SCHEMA = vol.Schema(
    {
        _required(CONF_BOILER_CLIMATE, "climate.buanderie_boiler_chauffe_eau"): entity("climate"),
        _required(CONF_BOILER_TEMP_SENSOR, "sensor.garage_boiler_sonde_temperature_temperature"): entity("sensor"),
        _required(CONF_BOILER_POWER_SENSOR, "sensor.boiler_puissance"): entity("sensor"),
        _required(CONF_BOILER_BINARY, "binary_sensor.boiler"): entity("binary_sensor"),
    }
)

PRI_SCHEMA = vol.Schema(
    {
        _required(CONF_PRI_L1, "switch.l1_pri"): entity("switch"),
        _required(CONF_PRI_L2, "switch.l2_pri"): entity("switch"),
        _required(CONF_PRI_L3, "switch.l3_pri"): entity("switch"),
        _required(CONF_PRI_L4, "switch.l4_pri"): entity("switch"),
    }
)

MACHINES_SCHEMA = vol.Schema(
    {
        _optional(CONF_WASHER_SOCKET, "switch.lave_linge_prise_1"): entity("switch"),
        _optional(CONF_WASHER_CYCLE, "input_boolean.lave_linge_en_cours"): entity(["binary_sensor", "input_boolean"]),
        vol.Optional(CONF_WASHER_ON_1, default="21:30:00"): selector.TimeSelector(),
        vol.Optional(CONF_WASHER_OFF_1, default="07:00:00"): selector.TimeSelector(),
        vol.Optional(CONF_WASHER_ON_2, default="10:30:00"): selector.TimeSelector(),
        vol.Optional(CONF_WASHER_OFF_2, default="17:00:00"): selector.TimeSelector(),
        _optional(CONF_DRYER_SOCKET, "switch.seche_linge_prise_1"): entity("switch"),
        _optional(CONF_DRYER_CYCLE, "input_boolean.seche_linge_en_cours"): entity(["binary_sensor", "input_boolean"]),
        vol.Optional(CONF_DRYER_ON_1, default="21:30:00"): selector.TimeSelector(),
        vol.Optional(CONF_DRYER_OFF_1, default="07:00:00"): selector.TimeSelector(),
        vol.Optional(CONF_DRYER_ON_2, default="10:30:00"): selector.TimeSelector(),
        vol.Optional(CONF_DRYER_OFF_2, default="17:00:00"): selector.TimeSelector(),
        _optional(CONF_DISHWASHER_SOCKET, "switch.lave_vaisselle_prise_1"): entity("switch"),
        _optional(CONF_DISHWASHER_CYCLE, "input_boolean.lave_vaisselle_en_cours"): entity(["binary_sensor", "input_boolean"]),
        vol.Optional(CONF_DISHWASHER_ON_1, default="21:30:00"): selector.TimeSelector(),
        vol.Optional(CONF_DISHWASHER_OFF_1, default="07:00:00"): selector.TimeSelector(),
        vol.Optional(CONF_DISHWASHER_ON_2, default="10:30:00"): selector.TimeSelector(),
        vol.Optional(CONF_DISHWASHER_OFF_2, default="17:00:00"): selector.TimeSelector(),
    }
)

PRICING_SCHEMA = vol.Schema(
    {
        _optional(CONF_PRICE_CURRENT, "sensor.luminus_luminus_dynamic_wallonia_prix_actuel"): entity("sensor"),
        _optional(CONF_PRICE_NEXT, "sensor.luminus_luminus_dynamic_wallonia_prix_heure_suivante"): entity("sensor"),
        _optional(CONF_PRICE_INJECTION, "sensor.luminus_luminus_dynamic_wallonia_prix_d_injection"): entity("sensor"),
        _optional(CONF_PRICE_MIN_TODAY, "sensor.luminus_luminus_dynamic_wallonia_minimum_aujourd_hui"): entity("sensor"),
        _optional(CONF_PRICE_MAX_TODAY, "sensor.luminus_luminus_dynamic_wallonia_maximum_aujourd_hui"): entity("sensor"),
        _optional(CONF_PRICE_AVG_TODAY, "sensor.luminus_luminus_dynamic_wallonia_moyenne_aujourd_hui"): entity("sensor"),
        _optional(CONF_PRICE_MIN_TOMORROW, "sensor.luminus_luminus_dynamic_wallonia_minimum_demain"): entity("sensor"),
        _optional(CONF_PRICE_MAX_TOMORROW, "sensor.luminus_luminus_dynamic_wallonia_maximum_demain"): entity("sensor"),
        _optional(CONF_PRICE_AVG_TOMORROW, "sensor.luminus_luminus_dynamic_wallonia_moyenne_demain"): entity("sensor"),
        _optional(CONF_PRICE_TOMORROW_AVAILABLE, "binary_sensor.luminus_luminus_dynamic_wallonia_prix_de_demain_disponibles"): entity("binary_sensor"),
    }
)

SOLAR_SCHEMA = vol.Schema(
    {
        _optional(CONF_AI_TASK, "ai_task.google_ai_task"): entity("ai_task"),
        _optional(CONF_FORECAST_NOW, "sensor.solar_production_forecast_production_d_electricite_estimee_maintenant"): entity("sensor"),
        _optional(CONF_FORECAST_THIS_HOUR, "sensor.solar_production_forecast_production_d_energie_estimee_cette_heure"): entity("sensor"),
        _optional(CONF_FORECAST_NEXT_HOUR, "sensor.solar_production_forecast_production_d_energie_estimee_heure_suivante"): entity("sensor"),
        _optional(CONF_FORECAST_TODAY, "sensor.solar_production_forecast_production_d_energie_estimee_aujourd_hui"): entity("sensor"),
        _optional(CONF_FORECAST_REMAINING_TODAY, "sensor.solar_production_forecast_production_d_energie_estimee_restante_aujourd_hui"): entity("sensor"),
        _optional(CONF_FORECAST_1H, "sensor.solar_production_forecast_production_d_energie_estimee_en_1_heure"): entity("sensor"),
        _optional(CONF_FORECAST_12H, "sensor.solar_production_forecast_production_d_energie_estimee_en_12_heures"): entity("sensor"),
        _optional(CONF_FORECAST_24H, "sensor.solar_production_forecast_production_d_energie_estimee_en_24_heures"): entity("sensor"),
        _optional(CONF_FORECAST_PEAK_TODAY, "sensor.solar_production_forecast_heure_de_pointe_de_puissance_la_plus_elevee_aujourd_hui"): entity("sensor"),
        _optional(CONF_FORECAST_TOMORROW, "sensor.solar_production_forecast_estimation_de_la_production_d_energie_demain"): entity("sensor"),
        _optional(CONF_FORECAST_PEAK_TOMORROW, "sensor.solar_production_forecast_heure_de_pointe_de_puissance_la_plus_elevee_demain"): entity("sensor"),
    }
)


class FoxCatEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_boiler()
        return self.async_show_form(step_id="user", data_schema=CORE_SCHEMA)

    async def async_step_boiler(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pri()
        return self.async_show_form(step_id="boiler", data_schema=BOILER_SCHEMA)

    async def async_step_pri(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_machines()
        return self.async_show_form(step_id="pri", data_schema=PRI_SCHEMA)

    async def async_step_machines(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pricing()
        return self.async_show_form(step_id="machines", data_schema=MACHINES_SCHEMA)

    async def async_step_pricing(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_solar()
        return self.async_show_form(step_id="pricing", data_schema=PRICING_SCHEMA)

    async def async_step_solar(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            title = str(self._data.get(CONF_INSTALLATION_NAME, "FoxCat Energy"))
            await self.async_set_unique_id("foxcat_energy_main")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=title, data=self._data)
        return self.async_show_form(step_id="solar", data_schema=SOLAR_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return FoxCatEnergyOptionsFlow(config_entry)


class FoxCatEnergyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["core", "boiler", "pri", "machines", "pricing", "solar", "finish"],
        )

    def _schema_with_current(self, schema: vol.Schema) -> vol.Schema:
        current = self.config_entry.data
        fields = {}
        for marker, validator in schema.schema.items():
            key = marker.schema
            if key in current:
                if isinstance(marker, vol.Required):
                    new_marker = vol.Required(key, default=current[key])
                else:
                    new_marker = vol.Optional(key, description={"suggested_value": current[key]})
            else:
                new_marker = marker
            fields[new_marker] = validator
        return vol.Schema(fields)

    async def _section(self, step_id: str, schema: vol.Schema, user_input):
        if user_input is not None:
            data = dict(self.config_entry.data)
            data.update(user_input)
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            return await self.async_step_init()
        return self.async_show_form(step_id=step_id, data_schema=self._schema_with_current(schema))

    async def async_step_core(self, user_input=None):
        return await self._section("core", CORE_SCHEMA, user_input)

    async def async_step_boiler(self, user_input=None):
        return await self._section("boiler", BOILER_SCHEMA, user_input)

    async def async_step_pri(self, user_input=None):
        return await self._section("pri", PRI_SCHEMA, user_input)

    async def async_step_machines(self, user_input=None):
        return await self._section("machines", MACHINES_SCHEMA, user_input)

    async def async_step_pricing(self, user_input=None):
        return await self._section("pricing", PRICING_SCHEMA, user_input)

    async def async_step_solar(self, user_input=None):
        return await self._section("solar", SOLAR_SCHEMA, user_input)

    async def async_step_finish(self, user_input=None):
        return self.async_create_entry(title="", data={})
