from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ACK_IDLE,
    ACK_NOK,
    ACK_OK,
    ACK_WAIT,
    BOILER_BOOST_65,
    BOILER_HEAT_45,
    BOILER_NONE,
    BOILER_STOP,
    CONF_AI_TASK,
    CONF_BOILER_BINARY,
    CONF_BOILER_CLIMATE,
    CONF_BOILER_POWER_SENSOR,
    CONF_BOILER_TEMP_SENSOR,
    CONF_DISHWASHER_CYCLE,
    CONF_DISHWASHER_SOCKET,
    CONF_DISHWASHER_ON_1,
    CONF_DISHWASHER_OFF_1,
    CONF_DISHWASHER_ON_2,
    CONF_DISHWASHER_OFF_2,
    CONF_DRYER_CYCLE,
    CONF_DRYER_SOCKET,
    CONF_DRYER_ON_1,
    CONF_DRYER_OFF_1,
    CONF_DRYER_ON_2,
    CONF_DRYER_OFF_2,
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
    CONF_HOUSE_SENSOR,
    CONF_INSTALLATION_NAME,
    CONF_MACHINES_V13,
    CONF_PRICE_AVG_TODAY,
    CONF_PRICE_AVG_TOMORROW,
    CONF_PRICE_CURRENT,
    CONF_PRICE_INJECTION,
    CONF_PRICE_MAX_TODAY,
    CONF_PRICE_MAX_TOMORROW,
    CONF_PRICE_MIN_TODAY,
    CONF_PRICE_MIN_TOMORROW,
    CONF_PRICE_NEXT,
    CONF_TARIFF_HP_START_1,
    CONF_TARIFF_HP_END_1,
    CONF_TARIFF_HP_START_2,
    CONF_TARIFF_HP_END_2,
    CONF_TARIFF_HP_PRICE,
    CONF_TARIFF_HC_PRICE,
    CONF_TARIFF_FIXED_INJECTION_PRICE,
    CONF_TARIFF_HP_PRICE_SENSOR,
    CONF_TARIFF_HC_PRICE_SENSOR,
    CONF_TARIFF_FIXED_INJECTION_PRICE_SENSOR,
    CONF_PRI_L1,
    CONF_PRI_L2,
    CONF_PRI_L3,
    CONF_PRI_L4,
    CONF_PV_SENSOR,
    CONF_WASHER_CYCLE,
    CONF_WASHER_SOCKET,
    CONF_WASHER_ON_1,
    CONF_WASHER_OFF_1,
    CONF_WASHER_ON_2,
    CONF_WASHER_OFF_2,
    DEFAULT_SETTINGS,
    DOMAIN,
    KNOWN_LEGACY_AUTOMATIONS,
    LEGACY_MODE_ENTITY,
    LEGACY_SETTING_MAP,
    LEGACY_SWITCH_MAP,
    MODE_ALIASES,
    MODE_DYNAMIC,
    MODE_ECO,
    MODE_ECS,
    MODE_MANUAL,
    MODE_ZERO,
    PHASE_ACQUISITION,
    PHASE_DECISION,
    PHASE_WAIT_ACK,
    RRCR_CODE_TO_LEVEL,
    RRCR_LEVEL_TO_CODE,
    TARIFF_COMPENSATION,
    TARIFF_DYNAMIC,
    TARIFF_TOU,
)
from .engine import EnergySnapshot, SolarForecast, decide_dynamic, decide_zero, evaluate_mode
from .engine.load_guard import (
    boiler_surplus_before_load_w,
    protected_cycle_boiler_allowed,
    protected_cycle_boiler_allowed_stable,
)
from .engine.tariff import price_status, tariff_boundaries, tariff_period
from .machines import MachineDefinition, machine_allowed, machine_definitions, schedule_boundaries
from .accounting import EnergyAccounting

_LOGGER = logging.getLogger(__name__)


class FoxCatEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Central sovereign EMS coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.config = dict(entry.data)
        self.config.update(entry.options)
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self.machines: list[MachineDefinition] = machine_definitions(self.config)
        self.settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.core_state: dict[str, Any] = {
            "phase": PHASE_ACQUISITION,
            "ack": ACK_IDLE,
            "last_reason": "FoxCat Energy initialisé.",
            "pending_action": "NONE",
            "pending_delta": 0.0,
            "action_reference_grid": 0.0,
            "grid_expected": 0.0,
            "ack_error": 0.0,
            "t0": None,
            "last_frame": None,
            "last_action": None,
            "boiler_demand": BOILER_NONE,
            "boiler_origin": "AUCUNE",
            "execution_status": "IDLE",
            "execution_command": "NONE",
            "execution_retries": 0,
            "execution_failure_reason": "",
        }
        self.pri_state: dict[str, Any] = {
            "current_level": 100,
            "target_level": 100,
            "code": "0000",
            "direction": "maintien",
            "ack_rrcr": "IDLE",
            "ack_inverter": "IDLE",
            "ack_grid": "IDLE",
            "score_current": 0.0,
            "score_target": 0.0,
            "house_target_level": 100,
            "last_reason": "PRI initialisé.",
            "frame_id": 0,
            "pending_frame_id": None,
            "pending_level": None,
            "pending_pv_before": None,
            "solar_state": "PV_UNKNOWN",
            "solar_potential_min_w": 0.0,
            "pv_limit_w": 4000.0,
            "pv_limit_error_w": 0.0,
        }
        self.solar_forecast = SolarForecast()
        self._unsubs: list[Any] = []
        self._core_lock = asyncio.Lock()
        self._action_lock = asyncio.Lock()
        self._pri_task: asyncio.Task | None = None
        self._execution_task: asyncio.Task | None = None
        self._pv_below_since: datetime | None = None
        self._last_boiler_command_at: datetime | None = None
        self._high_load_since: datetime | None = None
        self._high_load_below_since: datetime | None = None
        self._frame_id = 0
        self._high_load_high_frames = 0
        self._high_load_low_frames = 0
        self._sensor_reset_active = False
        self._valid_frames_after_reset = 0
        self.load_shed_state: dict[str, Any] = {
            "active": False,
            "reason": "Inactif",
            "triggered_at": None,
            "house_w": 0.0,
        }
        self._loaded_existing_state = False
        self.accounting = EnergyAccounting()

        super().__init__(
            hass,
            _LOGGER,
            name=f"FoxCat Energy {entry.entry_id}",
            update_interval=timedelta(seconds=30),
        )

    @property
    def installation_name(self) -> str:
        return str(self.config.get(CONF_INSTALLATION_NAME) or self.entry.title or "FoxCat Energy")

    async def async_initialize(self) -> None:
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            self.settings.update(stored.get("settings", {}))
            self.accounting.restore(stored.get("accounting"))
            sf = stored.get("solar_forecast")
            if isinstance(sf, dict):
                self.solar_forecast = SolarForecast(**{k: sf.get(k, getattr(SolarForecast(), k)) for k in SolarForecast.__dataclass_fields__})
            self._loaded_existing_state = True
        else:
            self._migrate_legacy_defaults()
            await self._async_save()

        # Les plages tarifaires sont des options de configuration. Elles sont
        # recopiées dans le contexte de stratégie à chaque chargement, sans
        # écraser les autres réglages persistants.
        for key in (CONF_TARIFF_HP_START_1, CONF_TARIFF_HP_END_1, CONF_TARIFF_HP_START_2, CONF_TARIFF_HP_END_2):
            if key in self.config and self.config.get(key) not in (None, ""):
                self.settings[key] = str(self.config[key])
        for key in (CONF_TARIFF_HP_PRICE, CONF_TARIFF_HC_PRICE, CONF_TARIFF_FIXED_INJECTION_PRICE):
            if key in self.config and self.config.get(key) not in (None, ""):
                try:
                    self.settings[key] = float(self.config[key])
                except (TypeError, ValueError):
                    pass

        # V1.3 : chaque machine extensible possède son propre interrupteur de gestion.
        # Les trois clés historiques restent utilisées pour les appareils migrés.
        for machine in self.machines:
            self.settings.setdefault(machine.setting_key, machine.automatic_default)

        self.settings["mode"] = MODE_ALIASES.get(str(self.settings.get("mode")), str(self.settings.get("mode")))
        self._register_listeners()
        await self.async_config_entry_first_refresh()

        if bool(self.settings.get("regulation_active")):
            # Power-cut/startup fail-safe: release inverter to 100% before regulation resumes.
            await self.async_release_pri_100("Démarrage Home Assistant : fail-safe onduleur 100 %.")
            await self.async_reconcile_machines()

    async def async_shutdown(self) -> None:
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:  # pragma: no cover - defensive
                pass
        self._unsubs.clear()
        if self._pri_task and not self._pri_task.done():
            self._pri_task.cancel()
        if self._execution_task and not self._execution_task.done():
            self._execution_task.cancel()
        await self._async_save()

    def _migrate_legacy_defaults(self) -> None:
        for key, entity_id in LEGACY_SETTING_MAP.items():
            state = self.hass.states.get(entity_id)
            if state and state.state not in {"unknown", "unavailable", "none", ""}:
                try:
                    self.settings[key] = float(state.state)
                except (TypeError, ValueError):
                    pass
        for key, entity_id in LEGACY_SWITCH_MAP.items():
            state = self.hass.states.get(entity_id)
            if state:
                self.settings[key] = state.state == STATE_ON
        mode = self.hass.states.get(LEGACY_MODE_ENTITY)
        if mode:
            self.settings["mode"] = MODE_ALIASES.get(mode.state, mode.state)

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "settings": self.settings,
                "accounting": self.accounting.dump(),
                "solar_forecast": {
                    "available": self.solar_forecast.available,
                    "start": self.solar_forecast.start,
                    "end": self.solar_forecast.end,
                    "confidence": self.solar_forecast.confidence,
                    "potential": self.solar_forecast.potential,
                    "trend": self.solar_forecast.trend,
                    "reason": self.solar_forecast.reason,
                    "raw": self.solar_forecast.raw,
                },
            }
        )

    def _register_listeners(self) -> None:
        house = self.config.get(CONF_HOUSE_SENSOR)
        if house:
            self._unsubs.append(async_track_state_change_event(self.hass, [house], self._on_house_event))

        # Le PRI zéro injection est piloté par les mesures réseau, pas par la
        # consommation maison. Toute nouvelle trame import/export peut relancer
        # une correction d'une marche.
        grid_entities = [eid for eid in [self.config.get(CONF_GRID_EXPORT_SENSOR), self.config.get(CONF_GRID_IMPORT_SENSOR)] if eid]
        if grid_entities:
            self._unsubs.append(async_track_state_change_event(self.hass, grid_entities, self._on_grid_event))

        machine_cycle_entities = [m.cycle_entity for m in self.machines if m.cycle_entity]
        safety_entities = [x for x in [self.config.get(CONF_BOILER_TEMP_SENSOR), self.config.get(CONF_BOILER_BINARY), self.config.get(CONF_BOILER_POWER_SENSOR), *machine_cycle_entities] if x]
        if safety_entities:
            self._unsubs.append(async_track_state_change_event(self.hass, safety_entities, self._on_safety_event))

        pv = self.config.get(CONF_PV_SENSOR)
        if pv:
            self._unsubs.append(async_track_state_change_event(self.hass, [pv], self._on_pv_event))

        price_entities = [
            eid
            for eid in [
                self.config.get(CONF_PRICE_CURRENT),
                self.config.get(CONF_PRICE_NEXT),
                self.config.get(CONF_PRICE_INJECTION),
                self.config.get(CONF_PRICE_MIN_TODAY),
                self.config.get(CONF_PRICE_MAX_TODAY),
                self.config.get(CONF_PRICE_AVG_TODAY),
                self.config.get(CONF_TARIFF_HP_PRICE_SENSOR),
                self.config.get(CONF_TARIFF_HC_PRICE_SENSOR),
                self.config.get(CONF_TARIFF_FIXED_INJECTION_PRICE_SENSOR),
            ]
            if eid
        ]
        if price_entities:
            self._unsubs.append(async_track_state_change_event(self.hass, price_entities, self._on_price_event))

        # Les bornes HP/HC sont configurables. Chaque transition force une
        # nouvelle acquisition pour éviter une décision sur l'ancien tarif.
        for hour, minute in sorted(tariff_boundaries(self.settings)):
            self._unsubs.append(async_track_time_change(self.hass, self._on_tariff_boundary, hour=hour, minute=minute, second=0))

        # Machine socket schedule reconciliation aux bornes configurées.
        # Les doublons sont fusionnés afin de ne créer qu'un listener par heure.
        for hour, minute in sorted(self._machine_schedule_boundaries()):
            self._unsubs.append(async_track_time_change(self.hass, self._on_machine_schedule, hour=hour, minute=minute, second=0))

        # EMS 2 schedule.
        for hour, minute, label in (
            (7, 0, "STRATÉGIE JOUR - TRANSITION HP 07:00"),
            (10, 30, "CONFIRMATION SOLAIRE 10:30"),
            (11, 0, "RÉÉVALUATION - TRANSITION HC 11:00"),
            (15, 0, "FAILSAFE THERMIQUE - 15:00 AVANT FIN HC"),
            (17, 0, "RÉÉVALUATION - TRANSITION HP 17:00"),
            (22, 0, "RÉÉVALUATION - TRANSITION HC NUIT 22:00"),
        ):
            self._unsubs.append(async_track_time_change(self.hass, lambda now, lbl=label: self.hass.async_create_task(self.async_analyze_solar(lbl)), hour=hour, minute=minute, second=0))

    @callback
    def _on_house_event(self, event: Event) -> None:
        self.hass.async_create_task(self.async_handle_house_frame())

    @callback
    def _on_grid_event(self, event: Event) -> None:
        self.hass.async_create_task(self.async_handle_grid_change())

    @callback
    def _on_safety_event(self, event: Event) -> None:
        self.hass.async_create_task(self.async_handle_safety_change())

    @callback
    def _on_pv_event(self, event: Event) -> None:
        self.hass.async_create_task(self.async_handle_pv_change())

    @callback
    def _on_price_event(self, event: Event) -> None:
        self.hass.async_create_task(self.async_handle_price_change())

    @callback
    def _on_tariff_boundary(self, now: datetime) -> None:
        self.reset_core("Transition tarifaire : nouvelle acquisition demandée.")
        self.async_set_updated_data(self._build_data())

    @callback
    def _on_machine_schedule(self, now: datetime) -> None:
        self.hass.async_create_task(self.async_reconcile_machines())

    async def _async_update_data(self) -> dict[str, Any]:
        await self._watchdog()
        await self._check_end_solar()
        if bool(self.settings.get("regulation_active")):
            await self._evaluate_high_load(self.snapshot())
        return self._build_data()

    def _float_state(self, entity_id: str | None, default: float = 0.0) -> float:
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if not state or state.state in {"unknown", "unavailable", "none", ""}:
            return default
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return default

    def _optional_float_state(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if not state or state.state in {"unknown", "unavailable", "none", ""}:
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _is_on(self, entity_id: str | None) -> bool:
        state = self.hass.states.get(entity_id) if entity_id else None
        return bool(state and state.state == STATE_ON)

    def _numeric_valid(self, entity_id: str | None) -> bool:
        return self._optional_float_state(entity_id) is not None

    def snapshot(self) -> EnergySnapshot:
        pv_id = self.config.get(CONF_PV_SENSOR)
        house_id = self.config.get(CONF_HOUSE_SENSOR)
        export_id = self.config.get(CONF_GRID_EXPORT_SENSOR)
        import_id = self.config.get(CONF_GRID_IMPORT_SENSOR)
        pv = self._float_state(pv_id)
        house = self._float_state(house_id)
        export = max(self._float_state(export_id), 0.0)
        imp = max(self._float_state(import_id), 0.0)
        boiler_power = max(self._float_state(self.config.get(CONF_BOILER_POWER_SENSOR)), 0.0)
        boiler_binary = self._is_on(self.config.get(CONF_BOILER_BINARY))
        boiler_on = boiler_binary or boiler_power > 200
        boiler_temp = self._float_state(self.config.get(CONF_BOILER_TEMP_SENSOR))
        climate = self.hass.states.get(self.config.get(CONF_BOILER_CLIMATE)) if self.config.get(CONF_BOILER_CLIMATE) else None
        try:
            setpoint = float(climate.attributes.get("temperature", self.settings["boiler_temp_normal_c"])) if climate else float(self.settings["boiler_temp_normal_c"])
        except (TypeError, ValueError):
            setpoint = float(self.settings["boiler_temp_normal_c"])
        machine_active = any(
            self._is_on(machine.cycle_entity)
            for machine in self.machines
            if machine.cycle_entity
        )
        valid = all(self._numeric_valid(eid) for eid in [pv_id, house_id, export_id, import_id])
        return EnergySnapshot(
            timestamp=dt_util.now(),
            pv_w=pv,
            house_w=house,
            export_w=export,
            import_w=imp,
            grid_net_w=export - imp,
            boiler_temp_c=boiler_temp,
            boiler_power_w=boiler_power,
            boiler_on=boiler_on,
            boiler_setpoint_c=setpoint,
            machine_active=machine_active,
            valid=valid,
        )

    def _boiler_on_seconds(self) -> float:
        """Return trusted physical ON duration for the boiler.

        The binary sensor is the sovereign cycle clock.  If power is already
        present but the binary sensor is not ON, the elapsed time is unknown:
        return 0 s rather than inventing a duration from the power sensor.
        """
        entity_id = self.config.get(CONF_BOILER_BINARY)
        state = self.hass.states.get(entity_id) if entity_id else None
        if state and state.state == STATE_ON:
            return max((dt_util.utcnow() - state.last_changed).total_seconds(), 0.0)
        power_id = self.config.get(CONF_BOILER_POWER_SENSOR)
        if self._float_state(power_id) > 200:
            return 0.0
        return 999999.0

    def prices(self) -> dict[str, Any]:
        """Build the tariff context used by modes and tariff sensors."""
        current = self._optional_float_state(self.config.get(CONF_PRICE_CURRENT))
        next_price = self._optional_float_state(self.config.get(CONF_PRICE_NEXT))
        injection = self._optional_float_state(self.config.get(CONF_PRICE_INJECTION))
        pmin = self._optional_float_state(self.config.get(CONF_PRICE_MIN_TODAY))
        pmax = self._optional_float_state(self.config.get(CONF_PRICE_MAX_TODAY))
        avg = self._optional_float_state(self.config.get(CONF_PRICE_AVG_TODAY))
        regime = str(self.settings.get("tariff_regime", TARIFF_COMPENSATION))
        period = tariff_period(dt_util.now(), self.settings)

        hp_manual = float(self.settings.get(CONF_TARIFF_HP_PRICE, 0.0))
        hc_manual = float(self.settings.get(CONF_TARIFF_HC_PRICE, 0.0))
        fixed_injection_manual = float(self.settings.get(CONF_TARIFF_FIXED_INJECTION_PRICE, 0.0))

        hp_sensor_id = self.config.get(CONF_TARIFF_HP_PRICE_SENSOR)
        hc_sensor_id = self.config.get(CONF_TARIFF_HC_PRICE_SENSOR)
        fixed_injection_sensor_id = self.config.get(CONF_TARIFF_FIXED_INJECTION_PRICE_SENSOR)
        hp_from_entity = self._optional_float_state(hp_sensor_id)
        hc_from_entity = self._optional_float_state(hc_sensor_id)
        fixed_injection_from_entity = self._optional_float_state(fixed_injection_sensor_id)

        hp_price = hp_from_entity if hp_from_entity is not None else hp_manual
        hc_price = hc_from_entity if hc_from_entity is not None else hc_manual
        fixed_injection = fixed_injection_from_entity if fixed_injection_from_entity is not None else fixed_injection_manual
        hp_source = hp_sensor_id if hp_from_entity is not None else "Valeur manuelle"
        hc_source = hc_sensor_id if hc_from_entity is not None else "Valeur manuelle"
        fixed_injection_source = fixed_injection_sensor_id if fixed_injection_from_entity is not None else "Valeur manuelle"

        active_buy: float | None
        export_value: float | None
        if regime == TARIFF_DYNAMIC:
            active_buy = current
            # Luminus Dynamic expose historiquement un prix d'injection signé :
            # une valeur négative signifie une rémunération. On normalise ici
            # en valeur économique positive pour les capteurs de coût.
            export_value = -injection if injection is not None else None
            status = price_status(current, pmin, pmax, avg)
            model = "DYNAMIQUE"
        else:
            active_buy = hp_price if period == "HP" else hc_price
            if regime == TARIFF_COMPENSATION:
                export_value = None
                status = f"COMPENSATION · {period}"
                model = "ESTIMATION_COMPENSATION"
            else:
                export_value = fixed_injection
                status = period
                model = "BIHORAIRE"
            if active_buy <= 0:
                status = f"{status} · PRIX À CONFIGURER"

        snap = self.snapshot()
        import_cost_rate = (snap.import_w / 1000.0 * active_buy) if active_buy is not None else None
        export_value_rate = (snap.export_w / 1000.0 * export_value) if export_value is not None else None
        net_cost_rate = None
        if import_cost_rate is not None:
            net_cost_rate = import_cost_rate - (export_value_rate or 0.0)

        negative_threshold = float(self.settings.get("dynamic_grid_charge_threshold_eur_kwh", 0.0))
        return {
            "hp_price": hp_price,
            "hc_price": hc_price,
            "fixed_injection_price": fixed_injection,
            "hp_price_source": hp_source,
            "hc_price_source": hc_source,
            "fixed_injection_price_source": fixed_injection_source,
            "current": current,
            "next": next_price,
            "injection": injection,
            "min_today": pmin,
            "max_today": pmax,
            "avg_today": avg,
            "min_tomorrow": self._optional_float_state(self.config.get(CONF_PRICE_MIN_TOMORROW)),
            "max_tomorrow": self._optional_float_state(self.config.get(CONF_PRICE_MAX_TOMORROW)),
            "avg_tomorrow": self._optional_float_state(self.config.get(CONF_PRICE_AVG_TOMORROW)),
            "regime": regime,
            "period": period,
            "status": status,
            "cost_model": model,
            "active_buy": active_buy,
            "export_value": export_value,
            "negative_purchase": bool(regime == TARIFF_DYNAMIC and active_buy is not None and active_buy < negative_threshold),
            "dynamic_compatible": regime == TARIFF_DYNAMIC,
            "import_cost_rate_eur_h": import_cost_rate,
            "export_value_rate_eur_h": export_value_rate,
            "net_cost_rate_eur_h": net_cost_rate,
        }


    def reset_core(self, reason: str) -> None:
        self.core_state.update(
            {
                "phase": PHASE_ACQUISITION,
                "ack": ACK_IDLE,
                "pending_action": "NONE",
                "pending_delta": 0.0,
                "ack_error": 0.0,
                "last_reason": reason,
            }
        )

    async def async_set_setting(self, key: str, value: Any) -> None:
        if key == "mode":
            await self.async_set_mode(str(value))
            return

        self.settings[key] = value

        if key == "regulation_active":
            if value:
                self.reset_core("Régulation FoxCat activée : acquisition requise.")
                await self.async_release_pri_100("Activation de la régulation : point de départ sûr à 100 %.")
                if str(self.settings.get("mode")) != MODE_MANUAL:
                    await self.async_reconcile_machines()
            else:
                self.reset_core("Régulation FoxCat désactivée.")
                if self._pri_task and not self._pri_task.done():
                    self._pri_task.cancel()
                await self.async_release_pri_100("Régulation désactivée : onduleur libéré à 100 %.")

        if key == "high_load_shed_enabled" and not value:
            self._high_load_since = None
            self._high_load_below_since = None
            if self.load_shed_state.get("active"):
                self.load_shed_state.update({"active": False, "reason": "Délestage désactivé", "triggered_at": None})
                if str(self.settings.get("mode")) != MODE_MANUAL:
                    await self.async_reconcile_machines()

        if key == "pri_enabled" and not value:
            if self._pri_task and not self._pri_task.done():
                self._pri_task.cancel()
            await self.async_release_pri_100("PRI désactivé par l'utilisateur.")

        if key in {"washer_enabled", "dryer_enabled", "dishwasher_enabled"}:
            await self.async_reconcile_machines()

        if key == "tariff_regime":
            self.reset_core(f"Régime tarifaire modifié vers {value} : nouvelle acquisition demandée.")
            if str(self.settings.get("mode")) == MODE_DYNAMIC:
                if str(value) == TARIFF_DYNAMIC:
                    self.settings["pri_enabled"] = True
                else:
                    self.settings["pri_enabled"] = False
                    if self._pri_task and not self._pri_task.done():
                        self._pri_task.cancel()
                    if bool(self.settings.get("regulation_active")):
                        await self.async_release_pri_100("Prix dynamique incompatible avec le régime tarifaire : onduleur libéré à 100 %.")
                        if self.snapshot().boiler_on:
                            await self.async_command_boiler(
                                BOILER_STOP,
                                "Régime tarifaire quitté : arrêt de la charge financière dynamique en cours.",
                                "PRIX_BLOQUE",
                            )

        await self._async_save()

        # HP/HC prices are configuration-backed since V1.2.2.  Keep the
        # editable number entities for backwards compatibility, but mirror any
        # change they make into ConfigEntry options so the dedicated tariff
        # page and the entities always survive restarts with the same value.
        if key in {CONF_TARIFF_HP_PRICE, CONF_TARIFF_HC_PRICE, CONF_TARIFF_FIXED_INJECTION_PRICE}:
            options = dict(self.entry.options)
            if options.get(key) != value:
                options[key] = value
                self.config[key] = value
                self.hass.config_entries.async_update_entry(self.entry, options=options)

        self.async_set_updated_data(self._build_data())

    async def async_set_mode(self, mode: str) -> None:
        canonical = MODE_ALIASES.get(mode, mode)
        self.settings["mode"] = canonical
        self.reset_core(f"Mode EMS modifié vers {canonical}. Cycle ACK annulé et nouvelle acquisition demandée.")
        self.core_state["boiler_demand"] = BOILER_NONE

        if self._pri_task and not self._pri_task.done():
            self._pri_task.cancel()

        if canonical == MODE_MANUAL:
            # Handover complet : pas de PRI, pas de planning machines, pas de
            # stratégie boiler. Le fail-safe met seulement le PRI à 100 % au
            # moment de la transition, puis l'utilisateur peut le forcer via
            # le sélecteur manuel 0..100 %.
            self.settings["pri_enabled"] = False
            if bool(self.settings.get("regulation_active")):
                await self.async_release_pri_100("Mode Manuel : remise initiale PRI à 100 %, puis main à l'utilisateur.")
            self.core_state["last_reason"] = "Mode Manuel : pilotages automatiques désactivés, sécurité thermique conservée."

        elif canonical == MODE_ECS:
            self.settings["pri_enabled"] = False
            if bool(self.settings.get("regulation_active")):
                await self.async_release_pri_100("Mode ECS solaire : PRI libéré à 100 %.")
                await self.async_reconcile_machines()

        elif canonical == MODE_DYNAMIC and str(self.settings.get("tariff_regime")) != TARIFF_DYNAMIC:
            self.settings["pri_enabled"] = False
            if bool(self.settings.get("regulation_active")):
                await self.async_release_pri_100("Mode Prix dynamique bloqué : régime tarifaire non dynamique.")
                await self.async_reconcile_machines()
            self.core_state["last_reason"] = "Prix dynamique bloqué : sélectionner le régime tarifaire Dynamique."

        elif canonical in {MODE_ECO, MODE_ZERO, MODE_DYNAMIC}:
            self.settings["pri_enabled"] = True
            if bool(self.settings.get("regulation_active")):
                # Repartir d'un état déterministe avant que la stratégie PRI
                # du nouveau mode ne reprenne la main.
                await self.async_release_pri_100(f"Mode {canonical} : initialisation PRI à 100 %.")
                await self.async_reconcile_machines()

        await self._async_save()
        self.async_set_updated_data(self._build_data())

    async def async_set_pri_manual_level(self, level: int) -> None:
        """Force un niveau RRCR uniquement lorsque le mode Manuel est actif."""
        if str(self.settings.get("mode")) != MODE_MANUAL:
            self.core_state["last_reason"] = "Commande PRI manuelle refusée : le mode EMS n'est pas Manuel."
            self.async_set_updated_data(self._build_data())
            return
        level = int(level)
        if level not in RRCR_LEVEL_TO_CODE:
            self.core_state["last_reason"] = f"Commande PRI manuelle invalide : {level} %."
            self.async_set_updated_data(self._build_data())
            return
        ok = await self._apply_rrcr_level(level)
        code = self._rrcr_code()
        expected = RRCR_LEVEL_TO_CODE[level]
        if ok and code == expected:
            self.pri_state.update({
                "current_level": level,
                "target_level": level,
                "code": code,
                "direction": "manuel",
                "ack_rrcr": "OK",
                "last_reason": f"Mode Manuel : niveau PRI forcé à {level} %.",
            })
            self.core_state["last_reason"] = f"Mode Manuel : onduleur PRI réglé à {level} %."
        else:
            self.pri_state["ack_rrcr"] = "FAILED"
            self.pri_state["last_reason"] = f"Échec commande manuelle PRI {level} % : code lu {code}, attendu {expected}."
        self.async_set_updated_data(self._build_data())

    async def async_handle_house_frame(self) -> None:
        """Traite uniquement une trame énergétique complète et valide.

        Les resets périodiques Smappee peuvent rendre brièvement les capteurs
        unknown/unavailable. Ces événements ne sont pas des trames EMS :
        - aucun frame_id n'est consommé ;
        - aucun ACK PRI N+1 n'est validé/échoué ;
        - l'intégrale PI est conservée ;
        - le niveau PRI est conservé ;
        - l'état du délestage est conservé ;
        - les cycles protégés et le boiler ne sont pas modifiés par optimisation.
        Après le retour des mesures, une trame complète de stabilisation est
        exigée avant de reprendre les décisions énergétiques.
        """
        async with self._core_lock:
            snapshot = self.snapshot()

            if not snapshot.valid:
                self._sensor_reset_active = True
                self._valid_frames_after_reset = 0
                self.core_state["last_reason"] = (
                    "Reset/indisponibilité capteurs : décisions EMS gelées, "
                    "PRI/ACK/délestage conservés."
                )
                self.pri_state["last_reason"] = (
                    "Mesures transitoirement invalides : PRI conservé, "
                    "état PRI conservé, attente d'une trame complète."
                )
                self.async_set_updated_data(self._build_data(snapshot))
                return

            if self._sensor_reset_active:
                self._valid_frames_after_reset += 1
                if self._valid_frames_after_reset < 2:
                    # Première trame valide après reset = stabilisation seulement.
                    self.core_state["last_reason"] = (
                        "Capteurs revenus : première trame valide de stabilisation, "
                        "aucune décision énergétique."
                    )
                    self.pri_state["last_reason"] = (
                        "Reprise capteurs : stabilisation N0, PRI inchangé."
                    )
                    self.async_set_updated_data(self._build_data(snapshot))
                    return
                self._sensor_reset_active = False
                self._valid_frames_after_reset = 0
                self.reset_core("Capteurs stabilisés après reset : reprise du CORE.")

            # Seules les vraies trames valides incrémentent N.
            self._frame_id += 1
            self.pri_state["frame_id"] = self._frame_id
            self.core_state["last_frame"] = snapshot.timestamp

            # Comptabilité énergétique : observe la trame, sans influencer le CORE.
            accounting_appliances = self.machine_states()
            accounting_appliances.append({
                "id": "boiler",
                "name": "Chauffe-eau",
                "power_w": snapshot.boiler_power_w,
            })
            if self.accounting.process(snapshot, self.prices(), accounting_appliances):
                self.hass.async_create_task(self._async_save())

            # Une commande faite sur N est vérifiée uniquement sur une vraie N+1.
            await self._validate_pending_pri_on_frame(snapshot)

            if bool(self.settings.get("regulation_active")):
                await self._evaluate_high_load(snapshot)
                await self._core_process_frame(snapshot)
                if not self.load_shed_state["active"]:
                    await self._run_pri_frame(snapshot)
            else:
                self.core_state["last_reason"] = "Régulation inactive : télémétrie seulement."

            self.async_set_updated_data(self._build_data(snapshot))

    async def async_handle_grid_change(self) -> None:
        """Télémétrie uniquement. Depuis 1.3.200, la trame maison est l'horloge CORE."""
        self.async_set_updated_data(self._build_data())

    async def _core_process_frame(self, snapshot: EnergySnapshot) -> None:
        if not snapshot.valid:
            self.reset_core("Mesures énergétiques invalides : aucune décision autorisée.")
            return

        # Le délestage haute consommation est prioritaire sur les stratégies
        # énergétiques normales, mais reste inactif en mode Manuel.
        if self.load_shed_state.get("active") and str(self.settings.get("mode")) != MODE_MANUAL:
            if snapshot.boiler_on:
                await self.async_command_boiler(
                    BOILER_STOP,
                    "Délestage haute consommation : arrêt temporaire du chauffe-eau.",
                    "DELESTAGE",
                )
            else:
                self.reset_core("Délestage haute consommation actif : charges variables suspendues.")
            return

        # Immediate thermal safety remains active in every mode.
        if snapshot.boiler_on and snapshot.boiler_temp_c >= float(self.settings["boiler_temp_safety_c"]):
            await self.async_command_boiler(BOILER_STOP, "SÉCURITÉ CORE : température boiler maximale atteinte.", "SECURITE")
            return

        # Un cycle machine protégé conserve la priorité, mais il ne condamne
        # plus le boiler par principe. Le boiler peut continuer si le surplus
        # réellement disponible après la machine couvre sa puissance.
        if (
            str(self.settings.get("mode")) != MODE_MANUAL
            and snapshot.boiler_on
            and snapshot.machine_active
            and not protected_cycle_boiler_allowed(snapshot, self.settings)
        ):
            await self.async_command_boiler(
                BOILER_STOP,
                "Cycle machine protégé : surplus solaire insuffisant pour alimenter simultanément le boiler.",
                "MACHINE",
            )
            return

        phase = self.core_state["phase"]
        if phase == PHASE_ACQUISITION:
            self.core_state["t0"] = snapshot
            self.core_state["phase"] = PHASE_DECISION
            self.core_state["ack"] = ACK_IDLE
            self.core_state["last_reason"] = (
                f"ACQUISITION : réseau={snapshot.grid_net_w:.0f} W "
                f"[export={snapshot.export_w:.0f} / import={snapshot.import_w:.0f}], "
                f"PV={snapshot.pv_w:.0f} W, maison={snapshot.house_w:.0f} W."
            )
            return

        if phase == PHASE_WAIT_ACK:
            self._validate_core_ack(snapshot)
            self.core_state["t0"] = snapshot
            self.core_state["phase"] = PHASE_ACQUISITION
            self.core_state["pending_action"] = "NONE"
            self.core_state["pending_delta"] = 0.0
            return

        if phase != PHASE_DECISION:
            self.reset_core("Phase CORE inconnue : retour ACQUISITION.")
            return

        t0: EnergySnapshot | None = self.core_state.get("t0")
        if not isinstance(t0, EnergySnapshot):
            self.reset_core("T0 absent : nouvelle acquisition requise.")
            return

        if abs(snapshot.grid_net_w - t0.grid_net_w) > float(self.settings["stability_tolerance_w"]):
            self.reset_core(
                f"Décision suspendue : variation réseau {abs(snapshot.grid_net_w - t0.grid_net_w):.0f} W > tolérance."
            )
            return

        mode = str(self.settings.get("mode"))
        if mode == MODE_MANUAL:
            self.reset_core("Mode Manuel : stratégies automatiques en sommeil, sécurités actives.")
            return

        intent = evaluate_mode(
            mode,
            snapshot,
            t0,
            self.settings,
            dt_util.now(),
            self._boiler_on_seconds(),
            str(self.core_state.get("boiler_demand", BOILER_NONE)),
            self.prices(),
            self.solar_forecast,
        )

        if (
            intent.action in {BOILER_HEAT_45, BOILER_BOOST_65}
            and snapshot.machine_active
            and not protected_cycle_boiler_allowed_stable(snapshot, t0, self.settings)
        ):
            available = max(snapshot.grid_net_w + (snapshot.boiler_power_w if snapshot.boiler_on else 0.0), 0.0)
            required = float(self.settings["boiler_power_w"])
            self.reset_core(
                f"Cycle machine protégé : boiler en attente, surplus disponible {available:.0f} W < {required:.0f} W requis."
            )
            return

        self.core_state["boiler_demand"] = intent.action
        self.core_state["boiler_origin"] = intent.origin
        self.core_state["last_reason"] = intent.reason

        if intent.action == BOILER_NONE:
            self.reset_core(intent.reason)
            return
        if intent.action == BOILER_STOP and not snapshot.boiler_on:
            self.reset_core(f"{intent.reason} Boiler déjà arrêté.")
            return
        if intent.action in {BOILER_HEAT_45, BOILER_BOOST_65} and snapshot.boiler_on:
            desired = float(self.settings["boiler_temp_normal_c"] if intent.action == BOILER_HEAT_45 else self.settings["boiler_temp_boost_c"])
            if abs(snapshot.boiler_setpoint_c - desired) < 0.6:
                self.reset_core(f"{intent.reason} Consigne déjà appliquée.")
                return
        await self.async_command_boiler(intent.action, intent.reason, intent.origin)

    def _validate_core_ack(self, snapshot: EnergySnapshot) -> None:
        reference = float(self.core_state.get("action_reference_grid", 0.0))
        expected = float(self.core_state.get("grid_expected", reference))
        delta = float(self.core_state.get("pending_delta", 0.0))
        action = str(self.core_state.get("pending_action", "NONE"))
        error = abs(snapshot.grid_net_w - expected)
        tolerance = float(self.settings["ack_tolerance_w"])
        direction_ok = False
        if action.startswith("BOILER_OFF") or action == "ECS_MODULE_OFF":
            direction_ok = snapshot.grid_net_w >= reference + delta * 0.50
        elif action in {"ECS_MODULE_ON_45", "ECS_MODULE_ON_65", "BOILER_ON_45", "BOILER_ON_45_GARANTIE", "BOILER_ON_45_PRICE"}:
            direction_ok = snapshot.grid_net_w <= reference - delta * 0.50
        elif action == "ECS_MODULE_UPGRADE_65":
            direction_ok = snapshot.boiler_on and snapshot.boiler_setpoint_c >= float(self.settings["boiler_temp_boost_c"]) - 1
        ok = error <= tolerance or direction_ok
        self.core_state["ack_error"] = error
        self.core_state["ack"] = ACK_OK if ok else ACK_NOK
        self.core_state["last_reason"] = (
            f"ACK {'OK' if ok else 'NOK'} : {action}. Référence={reference:.0f} W, "
            f"attendu={expected:.0f} W, réel={snapshot.grid_net_w:.0f} W, erreur={error:.0f} W."
        )

    async def async_command_boiler(self, action: str, reason: str, origin: str) -> None:
        if not bool(self.settings.get("regulation_active")):
            return
        climate = self.config.get(CONF_BOILER_CLIMATE)
        if not climate:
            self.core_state["execution_status"] = "FAILED"
            self.core_state["execution_failure_reason"] = "Climate boiler non configuré."
            return

        snap = self.snapshot()
        power = max(snap.boiler_power_w, float(self.settings["boiler_power_w"]))
        reference = snap.grid_net_w
        if action == BOILER_STOP:
            expected = reference + power
            pending = "BOILER_OFF_STRATEGY"
            delta = power
        elif action == BOILER_HEAT_45:
            expected = reference - float(self.settings["boiler_power_w"])
            pending = "ECS_MODULE_ON_45" if str(self.settings.get("mode")) == MODE_ECS else ("BOILER_ON_45_PRICE" if str(self.settings.get("mode")) == MODE_DYNAMIC else "BOILER_ON_45")
            delta = float(self.settings["boiler_power_w"])
        elif action == BOILER_BOOST_65:
            if snap.boiler_on:
                expected = reference
                pending = "ECS_MODULE_UPGRADE_65"
                delta = 0.0
            else:
                expected = reference - float(self.settings["boiler_power_w"])
                pending = "ECS_MODULE_ON_65"
                delta = float(self.settings["boiler_power_w"])
        else:
            return

        self.core_state.update(
            {
                "action_reference_grid": reference,
                "grid_expected": expected,
                "pending_delta": delta,
                "pending_action": pending,
                "ack": ACK_WAIT,
                "phase": PHASE_WAIT_ACK,
                "last_action": dt_util.now(),
                "boiler_origin": origin,
                "last_reason": reason,
                "execution_command": pending,
                "execution_status": "EXECUTION",
                "execution_retries": 0,
                "execution_failure_reason": "",
            }
        )

        async with self._action_lock:
            if action == BOILER_STOP:
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": climate, "hvac_mode": "off"}, blocking=True)
            else:
                target = float(self.settings["boiler_temp_normal_c"] if action == BOILER_HEAT_45 else self.settings["boiler_temp_boost_c"])
                await self.hass.services.async_call("climate", "set_temperature", {"entity_id": climate, "temperature": target}, blocking=True)
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": climate, "hvac_mode": "heat"}, blocking=True)

        self._last_boiler_command_at = dt_util.now()

        if self._execution_task and not self._execution_task.done():
            self._execution_task.cancel()
        self._execution_task = self.hass.async_create_task(self._verify_boiler_execution(pending))

    async def _verify_boiler_execution(self, command: str) -> None:
        try:
            for attempt in range(4):
                await asyncio.sleep(8 if attempt == 0 else 5)
                snap = self.snapshot()
                climate = self.hass.states.get(self.config.get(CONF_BOILER_CLIMATE)) if self.config.get(CONF_BOILER_CLIMATE) else None
                climate_state = climate.state if climate else "unavailable"
                setpoint = float(climate.attributes.get("temperature", 0)) if climate else 0.0
                command_off = command.startswith("BOILER_OFF") or command == "ECS_MODULE_OFF"
                command_boost = command in {"ECS_MODULE_ON_65", "ECS_MODULE_UPGRADE_65", "ECS_MODULE_SET_65"}
                logical_ok = climate_state == "off" if command_off else climate_state == "heat"
                if command_boost and not command_off:
                    logical_ok = logical_ok and setpoint >= float(self.settings["boiler_temp_boost_c"]) - 1
                physical_ok = (not snap.boiler_on) if command_off else snap.boiler_on
                if logical_ok and physical_ok:
                    self.core_state["execution_status"] = "OK"
                    self.core_state["execution_failure_reason"] = ""
                    self.core_state["execution_retries"] = attempt
                    self.async_set_updated_data(self._build_data())
                    return
                if attempt >= 3:
                    self.core_state["execution_status"] = "FAILED"
                    self.core_state["execution_retries"] = 3
                    self.core_state["execution_failure_reason"] = (
                        f"Commande {command} non exécutée après 3 tentatives. Climate={climate_state}, "
                        f"boiler={snap.boiler_power_w:.0f} W."
                    )
                    self.async_set_updated_data(self._build_data())
                    return
                if self._execution_blocked(command, snap):
                    self.core_state["execution_status"] = "BLOCKED"
                    self.core_state["execution_failure_reason"] = "Retry bloqué par sécurité, priorité machine, mode ou autorisation."
                    self.async_set_updated_data(self._build_data())
                    return
                self.core_state["execution_status"] = "RETRY"
                self.core_state["execution_retries"] = attempt + 1
                await self._retry_boiler_command(command)
        except asyncio.CancelledError:
            return
        except Exception as err:  # pragma: no cover - HA runtime defensive path
            _LOGGER.exception("FoxCat boiler verifier error: %s", err)
            self.core_state["execution_status"] = "FAILED"
            self.core_state["execution_failure_reason"] = str(err)

    def _execution_blocked(self, command: str, snap: EnergySnapshot) -> bool:
        command_on = not (command.startswith("BOILER_OFF") or command == "ECS_MODULE_OFF")
        if not command_on:
            return False
        if not bool(self.settings["boiler_enabled"]) or snap.boiler_temp_c >= float(self.settings["boiler_temp_safety_c"]):
            return True
        if snap.machine_active and not protected_cycle_boiler_allowed(snap, self.settings):
            return True
        if str(self.settings.get("mode")) == MODE_MANUAL:
            return True
        return False

    async def _retry_boiler_command(self, command: str) -> None:
        if not bool(self.settings.get("regulation_active")):
            return
        climate = self.config.get(CONF_BOILER_CLIMATE)
        if not climate:
            return
        async with self._action_lock:
            if command.startswith("BOILER_OFF") or command == "ECS_MODULE_OFF":
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": climate, "hvac_mode": "off"}, blocking=True)
            else:
                boost = command in {"ECS_MODULE_ON_65", "ECS_MODULE_UPGRADE_65", "ECS_MODULE_SET_65"}
                temp = float(self.settings["boiler_temp_boost_c"] if boost else self.settings["boiler_temp_normal_c"])
                await self.hass.services.async_call("climate", "set_temperature", {"entity_id": climate, "temperature": temp}, blocking=True)
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": climate, "hvac_mode": "heat"}, blocking=True)

    async def async_handle_safety_change(self) -> None:
        snap = self.snapshot()
        if bool(self.settings.get("regulation_active")):
            mode = str(self.settings.get("mode"))
            # La sécurité thermique dure reste active même en Manuel.
            if snap.boiler_on and snap.boiler_temp_c >= float(self.settings["boiler_temp_safety_c"]):
                await self.async_command_boiler(BOILER_STOP, "SÉCURITÉ : température boiler maximale atteinte.", "SECURITE")
            elif (
                mode != MODE_MANUAL
                and snap.boiler_on
                and snap.machine_active
                and not protected_cycle_boiler_allowed(snap, self.settings)
            ):
                await self.async_command_boiler(
                    BOILER_STOP,
                    "Cycle machine protégé : surplus solaire insuffisant pour maintenir le boiler.",
                    "MACHINE",
                )
            if mode != MODE_MANUAL:
                await self.async_reconcile_machines()
        self.async_set_updated_data(self._build_data(snap))

    @staticmethod
    def _time_minutes(value: Any, default: str) -> int:
        raw = str(value or default)
        try:
            parts = raw.split(":")
            return (int(parts[0]) % 24) * 60 + (int(parts[1]) % 60)
        except (ValueError, IndexError, TypeError):
            h, m = default.split(":")[:2]
            return int(h) * 60 + int(m)

    @staticmethod
    def _within_time_window(now_minute: int, start_minute: int, stop_minute: int) -> bool:
        if start_minute == stop_minute:
            return False
        if start_minute < stop_minute:
            return start_minute <= now_minute < stop_minute
        return now_minute >= start_minute or now_minute < stop_minute

    def _machine_allowed(self, machine_id: str, now: datetime) -> bool:
        machine = next((item for item in self.machines if item.machine_id == machine_id), None)
        return machine_allowed(machine, now) if machine else False

    def _machine_schedule_boundaries(self) -> set[tuple[int, int]]:
        return schedule_boundaries(self.machines)

    def machine_states(self) -> list[dict[str, Any]]:
        now = dt_util.now()
        result: list[dict[str, Any]] = []
        for machine in self.machines:
            result.append({
                "id": machine.machine_id,
                "name": machine.name,
                "switch": machine.switch_entity,
                "cycle_entity": machine.cycle_entity,
                "power_sensor": machine.power_sensor,
                "power_w": self._optional_float_state(machine.power_sensor),
                "cycle_active": self._is_on(machine.cycle_entity),
                "automatic": bool(self.settings.get(machine.setting_key, machine.automatic_default)),
                "sheddable": machine.sheddable,
                "window_open": machine_allowed(machine, now),
            })
        return result

    async def async_set_machine_enabled(self, machine_id: str, enabled: bool) -> None:
        machine = next((item for item in self.machines if item.machine_id == machine_id), None)
        if machine is None:
            return
        self.settings[machine.setting_key] = bool(enabled)
        await self._async_save()
        await self.async_reconcile_machines()
        self.async_set_updated_data(self._build_data())

    async def async_reconcile_machines(self) -> None:
        if not bool(self.settings.get("regulation_active")):
            return
        if str(self.settings.get("mode")) == MODE_MANUAL:
            # Manuel = handover complet. FoxCat ne change aucune prise machine.
            return
        now = dt_util.now()
        for machine in self.machines:
            socket = machine.switch_entity
            if not socket:
                continue
            cycle_active = self._is_on(machine.cycle_entity)
            management = bool(self.settings.get(machine.setting_key, machine.automatic_default))
            allowed = machine_allowed(machine, now)
            # Règle souveraine : un cycle déjà commencé n'est jamais interrompu.
            # Pendant un délestage, seules les machines explicitement délestables
            # et sans cycle protégé actif sont coupées.
            high_load_block = bool(self.load_shed_state.get("active")) and machine.sheddable and not cycle_active
            should_on = cycle_active or (management and allowed and not high_load_block)
            service = "turn_on" if should_on else "turn_off"
            try:
                await self.hass.services.async_call("switch", service, {"entity_id": socket}, blocking=False)
            except Exception as err:  # pragma: no cover
                _LOGGER.warning("FoxCat machine socket command failed for %s (%s): %s", machine.name, socket, err)

    async def _evaluate_high_load(self, snapshot: EnergySnapshot) -> None:
        """Délestage synchronisé sur la trame maison (30 s).

        2 trames hautes consécutives déclenchent. 5 trames basses réarment.
        Une mesure maison invalide gèle l'état et n'est jamais assimilée à 0 W.
        """
        house_id = self.config.get(CONF_HOUSE_SENSOR)
        if not self._numeric_valid(house_id):
            self.load_shed_state["reason"] = "Puissance maison inconnue : état de délestage conservé."
            self._high_load_high_frames = 0
            self._high_load_low_frames = 0
            return
        self.load_shed_state["house_w"] = snapshot.house_w
        enabled=bool(self.settings.get("high_load_shed_enabled"))
        automatic=str(self.settings.get("mode")) != MODE_MANUAL
        if not enabled or not automatic:
            self._high_load_high_frames=self._high_load_low_frames=0
            if self.load_shed_state.get("active"):
                self.load_shed_state.update({"active":False,"reason":"Délestage indisponible ou mode Manuel","triggered_at":None})
                await self.async_reconcile_machines()
            return
        trigger=float(self.settings.get("high_load_trigger_w",5000.0))
        release=min(float(self.settings.get("high_load_release_w",3500.0)),trigger)
        if not self.load_shed_state.get("active"):
            self._high_load_low_frames=0
            self._high_load_high_frames = self._high_load_high_frames + 1 if snapshot.house_w >= trigger else 0
            if self._high_load_high_frames >= 2:
                await self._activate_high_load_shed(snapshot,trigger)
                self._high_load_high_frames=0
        else:
            self._high_load_high_frames=0
            self._high_load_low_frames = self._high_load_low_frames + 1 if snapshot.house_w <= release else 0
            if self._high_load_low_frames >= 5:
                self.load_shed_state.update({"active":False,"reason":f"5 trames sous {release:.0f} W","triggered_at":None})
                self._high_load_low_frames=0
                self.reset_core("Fin délestage : 5 trames basses confirmées.")
                await self.async_reconcile_machines()

    async def _activate_high_load_shed(self, snapshot: EnergySnapshot, trigger_w: float) -> None:
        self.load_shed_state.update({
            "active": True,
            "reason": f"Puissance maison {snapshot.house_w:.0f} W >= {trigger_w:.0f} W",
            "triggered_at": dt_util.now(),
            "house_w": snapshot.house_w,
        })
        self._high_load_since = None
        self._high_load_below_since = None
        self.reset_core("Délestage haute consommation déclenché.")

        if self._pri_task and not self._pri_task.done():
            self._pri_task.cancel()
        # En forte demande, aucune raison de brider le photovoltaïque.
        await self.async_release_pri_100("Délestage haute consommation : onduleur libéré à 100 %.")

        if snapshot.boiler_on:
            await self.async_command_boiler(
                BOILER_STOP,
                "Délestage haute consommation : arrêt temporaire du chauffe-eau.",
                "DELESTAGE",
            )
        await self.async_reconcile_machines()

    async def async_handle_price_change(self) -> None:
        snap = self.snapshot()
        if (
            bool(self.settings.get("regulation_active"))
            and str(self.settings.get("mode")) == MODE_DYNAMIC
            and str(self.settings.get("tariff_regime")) == TARIFF_DYNAMIC
        ):
            # Un changement de prix doit pouvoir déclencher immédiatement le
            # mode financier, notamment le passage sous 0 €/kWh. On crée un T0
            # stable avec la mesure courante puis on évalue la stratégie.
            self.reset_core("Nouvelle trame tarifaire dynamique : réévaluation immédiate.")
            self.core_state["t0"] = snap
            self.core_state["phase"] = PHASE_DECISION
            await self._core_process_frame(snap)
            self._maybe_start_pri(snap)
        self.async_set_updated_data(self._build_data(snap))

    async def async_handle_pv_change(self) -> None:
        await self._check_end_solar()
        self.async_set_updated_data(self._build_data())

    async def _check_end_solar(self) -> None:
        if not bool(self.settings.get("regulation_active")):
            self._pv_below_since = None
            return
        mode = str(self.settings.get("mode"))
        if mode not in {MODE_ECO, MODE_ZERO}:
            self._pv_below_since = None
            return
        pv = self._float_state(self.config.get(CONF_PV_SENSOR))
        # Une production bridée ne mesure pas le potentiel solaire. À PRI <100 %,
        # et particulièrement à 0 %, FoxCat interdit toute conclusion "fin solaire".
        level = self._rrcr_level()
        if 0 <= level < 100 or self.pri_state.get("solar_state") in {"PV_LIMITED","PRI_ACK_PENDING","PV_UNKNOWN"}:
            self._pv_below_since = None
            return
        threshold = float(self.settings["pri_end_solar_w"])
        now = dt_util.now()
        if pv < threshold:
            if self._pv_below_since is None:
                self._pv_below_since = now
            elif (now - self._pv_below_since).total_seconds() >= float(self.settings["pri_end_solar_confirm_s"]):
                if self._pri_task and not self._pri_task.done():
                    self._pri_task.cancel()
                await self.async_release_pri_100("Fin solaire confirmée : onduleur libéré à 100 %.")
                await self.async_set_mode(MODE_ECS)
                self.core_state["last_reason"] = "Fin solaire confirmée : passage automatique en ECS solaire."
                self._pv_below_since = None
        else:
            self._pv_below_since = None

    async def _watchdog(self) -> None:
        last = self.core_state.get("last_frame")
        if not isinstance(last, datetime):
            return
        age = (dt_util.now() - last).total_seconds()
        if age > float(self.settings["watchdog_timeout_s"]):
            if self.core_state.get("phase") != PHASE_ACQUISITION:
                self.reset_core(f"Watchdog : aucune nouvelle trame depuis {age:.0f} s, machine d'états réinitialisée.")

    def _pri_settle_ok(self) -> bool:
        if self._last_boiler_command_at is None:
            return True
        age = (dt_util.now() - self._last_boiler_command_at).total_seconds()
        return age >= float(self.settings.get("pri_boiler_settle_s", 30.0))

    def _dynamic_tariff_ok(self) -> bool:
        return not (
            str(self.settings.get("mode")) == MODE_DYNAMIC
            and str(self.settings.get("tariff_regime")) != TARIFF_DYNAMIC
        )

    def _maybe_start_pri(self, snapshot: EnergySnapshot) -> None:
        """Compatibilité 1.3.x : aucune horloge PRI indépendante en 1.3.200."""
        return

    def _pri_guard(self) -> bool:
        """Autorise le PRI et expose la raison exacte d'un éventuel blocage."""
        if not bool(self.settings.get("regulation_active")):
            self.pri_state["guard_reason"] = "regulation_inactive"
            return False
        if not bool(self.settings.get("pri_enabled")):
            self.pri_state["guard_reason"] = "pri_disabled"
            return False
        if str(self.settings.get("mode")) not in {MODE_ECO, MODE_ZERO, MODE_DYNAMIC}:
            self.pri_state["guard_reason"] = f"mode_{self.settings.get('mode')}"
            return False
        if not self._dynamic_tariff_ok():
            self.pri_state["guard_reason"] = "dynamic_tariff_not_ready"
            return False
        if not self._pri_settle_ok():
            self.pri_state["guard_reason"] = "boiler_settle"
            return False
        if self.core_state.get("phase") == PHASE_WAIT_ACK:
            self.pri_state["guard_reason"] = "core_wait_boiler_ack"
            return False
        self.pri_state["guard_reason"] = "OK"
        return True


    def _rrcr_code(self) -> str:
        bits = []
        for key in (CONF_PRI_L4, CONF_PRI_L3, CONF_PRI_L2, CONF_PRI_L1):
            entity_id = self.config.get(key)
            state = self.hass.states.get(entity_id) if entity_id else None
            if not state or state.state not in {"on", "off"}:
                return "????"
            bits.append("1" if state.state == "on" else "0")
        return "".join(bits)

    def _rrcr_level(self) -> int:
        return RRCR_CODE_TO_LEVEL.get(self._rrcr_code(), -1)

    async def _apply_rrcr_level(self, level: int) -> bool:
        code = RRCR_LEVEL_TO_CODE.get(int(level))
        if code is None:
            return False
        entities = [self.config.get(CONF_PRI_L4), self.config.get(CONF_PRI_L3), self.config.get(CONF_PRI_L2), self.config.get(CONF_PRI_L1)]
        if not all(entities):
            return False
        async with self._action_lock:
            for entity_id, bit in zip(entities, code, strict=True):
                await self.hass.services.async_call("switch", "turn_on" if bit == "1" else "turn_off", {"entity_id": entity_id}, blocking=True)
        return True

    async def _wait_rrcr_code(self, code: str, timeout: float = 5.0) -> bool:
        end = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < end:
            if self._rrcr_code() == code:
                return True
            await asyncio.sleep(0.25)
        return self._rrcr_code() == code

    async def async_release_pri_100(self, reason: str) -> None:
        entities = [self.config.get(CONF_PRI_L1), self.config.get(CONF_PRI_L2), self.config.get(CONF_PRI_L3), self.config.get(CONF_PRI_L4)]
        if not all(entities):
            self.pri_state.update({"current_level": 100, "target_level": 100, "code": "0000", "last_reason": f"{reason} Relais PRI non configurés."})
            return
        try:
            await self._apply_rrcr_level(100)
            self.pri_state.update({"current_level": 100, "target_level": 100, "code": "0000", "direction": "maintien", "last_reason": reason, "ack_rrcr": "OK"})
        except Exception as err:  # pragma: no cover
            _LOGGER.warning("Unable to release PRI to 100%%: %s", err)
            self.pri_state["ack_rrcr"] = "FAILED"
            self.pri_state["last_reason"] = f"Échec fail-safe 100 % : {err}"

    def _update_pri_pv_comparator(self, snapshot: EnergySnapshot, level: int) -> None:
        max_w=float(self.settings.get("pri_step_w",400.0))*10.0
        limit=max_w*max(level,0)/100.0
        tol=float(self.settings.get("pri_pv_compare_tolerance_w",200.0))
        err=snapshot.pv_w-limit
        if level <= 0:
            state="PV_UNKNOWN"
            potential=0.0
        elif abs(err) <= tol:
            state="PV_LIMITED"
            potential=max(limit-tol,0.0)
        elif snapshot.pv_w < limit-tol:
            state="PV_BELOW_LIMIT"
            potential=max(snapshot.pv_w,0.0)
        else:
            state="PRI_INCONSISTENT"
            potential=max(snapshot.pv_w,0.0)
        self.pri_state.update({"solar_state":state,"solar_potential_min_w":potential,
                               "pv_limit_w":limit,"pv_limit_error_w":err})

    async def _validate_pending_pri_on_frame(self, snapshot: EnergySnapshot) -> None:
        if not snapshot.valid:
            return
        pending=self.pri_state.get("pending_level")
        pending_frame=self.pri_state.get("pending_frame_id")
        if pending is None or pending_frame is None or self._frame_id <= int(pending_frame):
            return
        level=self._rrcr_level()
        if level != int(pending):
            self.pri_state["ack_rrcr"]="FAILED"
            self.pri_state["last_reason"]=f"ACK N+1 : RRCR {level}% != commande {pending}%."
        else:
            self.pri_state["ack_rrcr"]="OK"
            self._update_pri_pv_comparator(snapshot,level)
            self.pri_state["ack_inverter"]="OK" if self.pri_state["solar_state"]!="PRI_INCONSISTENT" else "FAILED"
            self.pri_state["ack_grid"]=self._classify_pri_grid(snapshot)
        self.pri_state["pending_level"]=None
        self.pri_state["pending_frame_id"]=None
        self.pri_state["pending_pv_before"]=None

    async def _run_pri_frame(self, snapshot: EnergySnapshot) -> None:
        """PRI classique : comparaison des marches adjacentes, une marche max/trame."""
        if not snapshot.valid:
            self.pri_state["last_reason"] = "PRI gelé : snapshot énergétique incomplet."
            return
        if not self._pri_guard():
            return
        if self.pri_state.get("pending_level") is not None:
            self.pri_state["last_reason"] = (
                f"PRI en attente de validation N+1 (commande "
                f"{self.pri_state.get('pending_level')} %)."
            )
            return

        current = self._rrcr_level()
        if current < 0:
            self.pri_state.update({"ack_rrcr":"FAILED","last_reason":"Code RRCR inconnu."})
            return

        self._update_pri_pv_comparator(snapshot, current)
        mode = str(self.settings.get("mode"))
        if mode == MODE_DYNAMIC:
            decision = decide_dynamic(
                snapshot, current, self.settings,
                self.prices().get("injection"), snapshot.boiler_on
            )
        else:
            decision = decide_zero(snapshot, current, self.settings)

        target = int(decision.target_level)
        if target > current:
            target = min(current + 10, 100)
        elif target < current:
            target = max(current - 10, 0)

        direction = "remontee" if target > current else "descente" if target < current else "maintien"
        self.pri_state.update({
            "current_level": current, "target_level": target,
            "direction": direction, "last_reason": decision.reason
        })

        if target == current:
            self.pri_state["ack_grid"] = self._classify_pri_grid(snapshot)
            return

        target_code = RRCR_LEVEL_TO_CODE[target]
        await self._apply_rrcr_level(target)
        if not await self._wait_rrcr_code(target_code):
            self.pri_state["ack_rrcr"] = "FAILED"
            self.pri_state["last_reason"] = (
                f"PRI classique : RRCR {target}% non confirmé, retour {current}%."
            )
            await self._apply_rrcr_level(current)
            return

        self.pri_state.update({
            "ack_rrcr":"PENDING","ack_inverter":"PENDING","ack_grid":"PENDING",
            "pending_level":target,"pending_frame_id":self._frame_id,
            "pending_pv_before":snapshot.pv_w
        })

    async def async_reset_cycle(self) -> None:
        self.reset_core("Cycle EMS réinitialisé manuellement.")
        if self._pri_task and not self._pri_task.done():
            self._pri_task.cancel()
        self.pri_state.update({"ack_rrcr": "IDLE", "ack_inverter": "IDLE", "ack_grid": "IDLE", "last_reason": "Cycle PRI réinitialisé."})
        self.async_set_updated_data(self._build_data())

    async def async_diagnostic(self) -> None:
        snap = self.snapshot()
        missing = []
        for key, label in ((CONF_PV_SENSOR, "PV"), (CONF_HOUSE_SENSOR, "maison"), (CONF_GRID_EXPORT_SENSOR, "export"), (CONF_GRID_IMPORT_SENSOR, "import")):
            if not self._numeric_valid(self.config.get(key)):
                missing.append(label)
        legacy_on = [eid for eid in KNOWN_LEGACY_AUTOMATIONS if self._is_on(eid)]
        parts = []
        if missing:
            parts.append("Capteurs invalides : " + ", ".join(missing))
        else:
            parts.append("Mesures principales valides")
        if legacy_on:
            parts.append("automatisations legacy actives : " + ", ".join(legacy_on))
        parts.append(f"réseau={snap.grid_net_w:.0f} W")
        parts.append(f"PRI={self._rrcr_level()} %")
        self.core_state["last_reason"] = "Diagnostic FoxCat : " + " | ".join(parts)
        self.async_set_updated_data(self._build_data(snap))

    async def async_analyze_solar(self, analysis_type: str = "RÉÉVALUATION MANUELLE") -> None:
        if not bool(self.settings.get("solar_advisor_enabled")):
            return
        ai_entity = self.config.get(CONF_AI_TASK)
        if ai_entity and self.hass.services.has_service("ai_task", "generate_data"):
            try:
                prompt = self._solar_prompt(analysis_type)
                structure = {
                    "decision": {"selector": {"select": {"options": ["OUI", "NON"]}}},
                    "debut": {"selector": {"text": {}}},
                    "fin": {"selector": {"text": {}}},
                    "confiance": {"selector": {"number": {"min": 0, "max": 100, "step": 1}}},
                    "potentiel": {"selector": {"select": {"options": ["Aucun", "Faible", "Moyen", "Bon", "Fort"]}}},
                    "tendance": {"selector": {"select": {"options": ["NOUVELLE", "CONFIRMÉE", "DÉCALÉE", "DÉGRADÉE", "ANNULÉE"]}}},
                    "justification": {"selector": {"text": {}}},
                }
                response = await self.hass.services.async_call(
                    "ai_task",
                    "generate_data",
                    {"entity_id": ai_entity, "task_name": f"EMS 2 - Prévision solaire - {analysis_type}", "instructions": prompt, "structure": structure},
                    blocking=True,
                    return_response=True,
                )
                payload = response.get("data", response) if isinstance(response, dict) else {}
                decision = str(payload.get("decision", "NON"))
                potential = str(payload.get("potentiel", "Aucun"))
                trend = str(payload.get("tendance", "NOUVELLE"))
                if decision in {"OUI", "NON"} and potential in {"Aucun", "Faible", "Moyen", "Bon", "Fort"} and trend in {"NOUVELLE", "CONFIRMÉE", "DÉCALÉE", "DÉGRADÉE", "ANNULÉE"}:
                    self.solar_forecast = SolarForecast(
                        available=decision == "OUI",
                        start=str(payload.get("debut", "--:--")),
                        end=str(payload.get("fin", "--:--")),
                        confidence=max(0.0, min(100.0, float(payload.get("confiance", 0)))),
                        potential=potential,
                        trend=trend,
                        reason=str(payload.get("justification", ""))[:255],
                        raw=f"{decision} | {payload.get('debut','--:--')}-{payload.get('fin','--:--')} | {payload.get('confiance',0)}% | {potential} | {trend}",
                    )
                    await self._async_save()
                    self.async_set_updated_data(self._build_data())
                    return
            except Exception as err:  # pragma: no cover
                _LOGGER.warning("EMS 2 AI Task failed, deterministic fallback used: %s", err)
        self._deterministic_solar_fallback(analysis_type)
        await self._async_save()
        self.async_set_updated_data(self._build_data())

    def _deterministic_solar_fallback(self, analysis_type: str) -> None:
        values = [
            self._optional_float_state(self.config.get(CONF_FORECAST_NOW)),
            self._optional_float_state(self.config.get(CONF_FORECAST_1H)),
            self._optional_float_state(self.config.get(CONF_FORECAST_NEXT_HOUR)),
        ]
        numeric = [v for v in values if v is not None]
        power = max(numeric) if numeric else 0.0
        min_w = float(self.settings["solar_threshold_min_w"])
        possible = float(self.settings["solar_threshold_possible_w"])
        good = float(self.settings["solar_threshold_good_w"])
        strong = float(self.settings["solar_threshold_strong_w"])
        if power >= strong:
            potential, confidence = "Fort", 85.0
        elif power >= good:
            potential, confidence = "Bon", 78.0
        elif power >= possible:
            potential, confidence = "Moyen", 70.0
        elif power >= min_w:
            potential, confidence = "Faible", 55.0
        else:
            potential, confidence = "Aucun", 30.0
        available = potential in {"Moyen", "Bon", "Fort"} and confidence >= float(self.settings["solar_confidence_min_percent"])
        peak_state = self.hass.states.get(self.config.get(CONF_FORECAST_PEAK_TODAY)) if self.config.get(CONF_FORECAST_PEAK_TODAY) else None
        peak = peak_state.state if peak_state and peak_state.state not in {"unknown", "unavailable"} else "--:--"
        self.solar_forecast = SolarForecast(
            available=available,
            start=peak if available else "--:--",
            end="--:--",
            confidence=confidence,
            potential=potential,
            trend="NOUVELLE",
            reason=f"Fallback local {analysis_type.lower()} : potentiel {potential.lower()}.",
            raw=f"{'OUI' if available else 'NON'} | {peak}---:-- | {confidence:.0f}% | {potential} | NOUVELLE",
        )

    def _solar_prompt(self, analysis_type: str) -> str:
        snap = self.snapshot()
        def st(key: str) -> str:
            eid = self.config.get(key)
            state = self.hass.states.get(eid) if eid else None
            return state.state if state else "indisponible"
        return f"""Tu es EMS 2, module prédictif solaire de FoxCat Energy. Tu es uniquement consultatif : ne commande aucun équipement et ne modifies aucune consigne. EMS 1 reste seul décisionnaire.

Analyse: {analysis_type}
Date/heure: {dt_util.now().strftime('%d/%m/%Y %H:%M')}
PV réel: {snap.pv_w:.0f} W
Maison réelle: {snap.house_w:.0f} W
Export compteur: {snap.export_w:.0f} W
Import compteur: {snap.import_w:.0f} W
Température boiler: {snap.boiler_temp_c:.1f} °C
Confort minimal: {float(self.settings['boiler_temp_normal_c']):.0f} °C
HC: 22:00-07:00 et 11:00-17:00. HP: 07:00-11:00 et 17:00-22:00.
Forecast maintenant: {st(CONF_FORECAST_NOW)}
Cette heure: {st(CONF_FORECAST_THIS_HOUR)}
Heure suivante: {st(CONF_FORECAST_NEXT_HOUR)}
Restant aujourd'hui: {st(CONF_FORECAST_REMAINING_TODAY)}
Pic aujourd'hui: {st(CONF_FORECAST_PEAK_TODAY)}
Demain: {st(CONF_FORECAST_TOMORROW)}
Pic demain: {st(CONF_FORECAST_PEAK_TOMORROW)}

Cherche une fenêtre solaire exploitable avant la prochaine échéance énergétique pertinente. Une faible production actuelle n'annule pas une fenêtre future. Ne confonds pas production PV et surplus disponible. Si plusieurs fenêtres existent, choisis une seule fenêtre, stable et durable. À 15:00, privilégie la garantie thermique avant 17:00. Fournis uniquement les champs structurés demandés. Justification: maximum 12 mots."""

    def _legacy_conflict(self) -> bool:
        return any(self._is_on(eid) for eid in KNOWN_LEGACY_AUTOMATIONS)

    def _build_data(self, snapshot: EnergySnapshot | None = None) -> dict[str, Any]:
        snap = snapshot or self.snapshot()
        rrcr_code = self._rrcr_code() if all(self.config.get(k) for k in (CONF_PRI_L1, CONF_PRI_L2, CONF_PRI_L3, CONF_PRI_L4)) else "----"
        level = RRCR_CODE_TO_LEVEL.get(rrcr_code, -1)
        self.pri_state["current_level"] = level
        self.pri_state["code"] = rrcr_code
        return {
            "snapshot": snap,
            "settings": dict(self.settings),
            "core": dict(self.core_state),
            "pri": dict(self.pri_state),
            "solar": self.solar_forecast,
            "prices": self.prices(),
            "accounting": self.accounting.view(),
            "legacy_conflict": self._legacy_conflict(),
            "load_shed": dict(self.load_shed_state),
            "machine_guard": {
                "active": snap.machine_active,
                "boiler_surplus_available_w": boiler_surplus_before_load_w(snap),
                "boiler_allowed": protected_cycle_boiler_allowed(snap, self.settings),
            },
            "machines": self.machine_states(),
            "machine_window": {machine.machine_id: machine_allowed(machine, dt_util.now()) for machine in self.machines},
        }
