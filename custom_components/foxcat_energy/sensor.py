from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FoxCatEnergyCoordinator
from .entity import FoxCatEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c: FoxCatEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        FoxCatValueSensor(c, "phase", "Phase de régulation", "mdi:state-machine", "ems", lambda d: d["core"]["phase"]),
        FoxCatValueSensor(c, "ack", "Validation d’exécution EMS", "mdi:check-decagram-outline", "ems", lambda d: d["core"]["ack"]),
        FoxCatValueSensor(c, "derniere_raison", "Dernière décision EMS", "mdi:information-outline", "ems", lambda d: d["core"]["last_reason"]),
        FoxCatValueSensor(c, "action_en_attente", "Action en attente", "mdi:progress-clock", "ems", lambda d: d["core"]["pending_action"]),
        FoxCatValueSensor(c, "demande_boiler", "Demande chauffe-eau", "mdi:water-boiler-auto", "boiler", lambda d: d["core"]["boiler_demand"]),
        FoxCatValueSensor(c, "origine_boiler", "Origine de la demande chauffe-eau", "mdi:source-branch", "boiler", lambda d: d["core"]["boiler_origin"]),
        FoxCatValueSensor(c, "execution_status", "État d’exécution chauffe-eau", "mdi:progress-check", "boiler", lambda d: d["core"]["execution_status"]),
        FoxCatValueSensor(c, "execution_command", "Commande chauffe-eau vérifiée", "mdi:code-tags-check", "boiler", lambda d: d["core"]["execution_command"]),
        FoxCatValueSensor(c, "execution_failure_reason", "Raison d'échec d'exécution", "mdi:alert-circle-outline", "boiler", lambda d: d["core"]["execution_failure_reason"] or "Aucune"),
        FoxCatNumericSensor(c, "execution_retries", "Tentatives d'exécution", "mdi:counter", "boiler", lambda d: d["core"]["execution_retries"]),
        FoxCatNumericSensor(c, "erreur_ack", "Erreur ACK", "mdi:delta", "ems", lambda d: d["core"]["ack_error"], UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "reseau_reference_action", "Réseau avant action", "mdi:transmission-tower", "ems", lambda d: d["core"]["action_reference_grid"], UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "reseau_attendu", "Réseau attendu", "mdi:transmission-tower", "ems", lambda d: d["core"]["grid_expected"], UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "variation_attendue", "Variation attendue", "mdi:swap-vertical", "ems", lambda d: d["core"]["pending_delta"], UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "production_pv", "Puissance de production photovoltaïque", "mdi:solar-power", "ems", lambda d: d["snapshot"].pv_w, UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "consommation_maison", "Puissance de consommation maison", "mdi:home-lightning-bolt", "ems", lambda d: d["snapshot"].house_w, UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatValueSensor(c, "statut_delestage", "Statut délestage haute consommation", "mdi:home-lightning-bolt-outline", "ems", lambda d: d["load_shed"].get("reason")),
        FoxCatNumericSensor(c, "reinjection_reseau", "Puissance réinjectée au réseau", "mdi:transmission-tower-export", "ems", lambda d: d["snapshot"].export_w, UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "prelevement_reseau", "Puissance prélevée au réseau", "mdi:transmission-tower-import", "ems", lambda d: d["snapshot"].import_w, UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "balance_reseau", "Puissance nette réseau", "mdi:transmission-tower", "ems", lambda d: d["snapshot"].grid_net_w, UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "temperature_boiler", "Température chauffe-eau", "mdi:thermometer-water", "boiler", lambda d: d["snapshot"].boiler_temp_c, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        FoxCatNumericSensor(c, "puissance_boiler", "Puissance chauffe-eau", "mdi:water-boiler", "boiler", lambda d: d["snapshot"].boiler_power_w, UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "pri_niveau_actuel", "Niveau de puissance PRI actuel", "mdi:solar-power-variant", "pri", lambda d: d["pri"]["current_level"], PERCENTAGE),
        FoxCatNumericSensor(c, "pri_niveau_cible", "Niveau de puissance PRI cible", "mdi:target", "pri", lambda d: d["pri"]["target_level"], PERCENTAGE),
        FoxCatValueSensor(c, "pri_code_rrcr", "Code RRCR", "mdi:code-binary", "pri", lambda d: d["pri"]["code"]),
        FoxCatValueSensor(c, "pri_direction", "Direction PRI", "mdi:arrow-up-down", "pri", lambda d: d["pri"]["direction"]),
        FoxCatValueSensor(c, "pri_ack_rrcr", "ACK RRCR", "mdi:electric-switch", "pri", lambda d: d["pri"]["ack_rrcr"]),
        FoxCatValueSensor(c, "pri_ack_onduleur", "ACK onduleur", "mdi:solar-power", "pri", lambda d: d["pri"]["ack_inverter"]),
        FoxCatValueSensor(c, "pri_ack_reseau", "ACK réseau", "mdi:transmission-tower", "pri", lambda d: d["pri"]["ack_grid"]),
        FoxCatValueSensor(c, "pri_derniere_raison", "Dernière décision PRI", "mdi:information-outline", "pri", lambda d: d["pri"]["last_reason"]),
        FoxCatNumericSensor(c, "pri_score_actuel", "Score PRI actuel", "mdi:scale-balance", "pri", lambda d: d["pri"]["score_current"]),
        FoxCatNumericSensor(c, "pri_score_cible", "Score PRI cible", "mdi:scale-balance", "pri", lambda d: d["pri"]["score_target"]),
        FoxCatNumericSensor(c, "pri_cible_maison", "Repère PRI selon consommation (diagnostic)", "mdi:home-percent-outline", "pri", lambda d: d["pri"]["house_target_level"], PERCENTAGE),
        FoxCatNumericSensor(c, "confiance_solaire", "Confiance solaire", "mdi:weather-sunny-alert", "solar", lambda d: d["solar"].confidence, PERCENTAGE),
        FoxCatValueSensor(c, "potentiel_solaire", "Potentiel solaire", "mdi:white-balance-sunny", "solar", lambda d: d["solar"].potential),
        FoxCatValueSensor(c, "tendance_solaire", "Tendance solaire", "mdi:trending-up", "solar", lambda d: d["solar"].trend),
        FoxCatValueSensor(c, "prevision_solaire_debut", "Début fenêtre solaire", "mdi:clock-start", "solar", lambda d: d["solar"].start),
        FoxCatValueSensor(c, "prevision_solaire_fin", "Fin fenêtre solaire", "mdi:clock-end", "solar", lambda d: d["solar"].end),
        FoxCatValueSensor(c, "prevision_solaire_raison", "Raison prévision solaire", "mdi:text-box-outline", "solar", lambda d: d["solar"].reason),
        FoxCatValueSensor(c, "prevision_solaire_brute", "Prévision solaire brute", "mdi:code-json", "solar", lambda d: d["solar"].raw),
        FoxCatNumericSensor(c, "prix_actuel", "Prix dynamique actuel", "mdi:cash", "pricing", lambda d: d["prices"].get("current"), "€/kWh"),
        FoxCatNumericSensor(c, "prix_suivant", "Prix dynamique heure suivante", "mdi:cash-clock", "pricing", lambda d: d["prices"].get("next"), "€/kWh"),
        FoxCatNumericSensor(c, "prix_injection", "Prix dynamique de réinjection brut", "mdi:cash-plus", "pricing", lambda d: d["prices"].get("injection"), "€/kWh"),
        FoxCatNumericSensor(c, "prix_heures_pleines", "Prix heures pleines (HP)", "mdi:cash-clock", "pricing", lambda d: d["prices"].get("hp_price"), "€/kWh"),
        FoxCatNumericSensor(c, "prix_heures_creuses", "Prix heures creuses (HC)", "mdi:cash-clock-outline", "pricing", lambda d: d["prices"].get("hc_price"), "€/kWh"),
        FoxCatNumericSensor(c, "prix_reinjection_fixe", "Prix fixe de réinjection", "mdi:transmission-tower-export", "pricing", lambda d: d["prices"].get("fixed_injection_price"), "€/kWh"),
        FoxCatValueSensor(c, "source_prix_hp", "Source prix heures pleines", "mdi:database-arrow-right-outline", "pricing", lambda d: d["prices"].get("hp_price_source")),
        FoxCatValueSensor(c, "source_prix_hc", "Source prix heures creuses", "mdi:database-arrow-right-outline", "pricing", lambda d: d["prices"].get("hc_price_source")),
        FoxCatValueSensor(c, "source_prix_reinjection_fixe", "Source prix fixe de réinjection", "mdi:database-arrow-right-outline", "pricing", lambda d: d["prices"].get("fixed_injection_price_source")),
        FoxCatNumericSensor(c, "surplus_disponible_boiler_cycle_protege", "Surplus disponible pour le chauffe-eau pendant cycle protégé", "mdi:solar-power-variant-outline", "machines", lambda d: d["machine_guard"].get("boiler_surplus_available_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatValueSensor(c, "regime_tarifaire_actif", "Régime tarifaire actif", "mdi:cash-sync", "pricing", lambda d: d["prices"].get("regime")),
        FoxCatValueSensor(c, "periode_tarifaire", "Période tarifaire", "mdi:clock-time-eight-outline", "pricing", lambda d: d["prices"].get("period")),
        FoxCatValueSensor(c, "statut_prix", "Statut du prix", "mdi:chart-line", "pricing", lambda d: d["prices"].get("status")),
        FoxCatValueSensor(c, "modele_cout", "Modèle de coût", "mdi:calculator-variant-outline", "pricing", lambda d: d["prices"].get("cost_model")),
        FoxCatValueSensor(c, "prix_negatif_actif", "Prix dynamique négatif actif", "mdi:cash-minus", "pricing", lambda d: "OUI" if d["prices"].get("negative_purchase") else "NON"),
        FoxCatNumericSensor(c, "prix_achat_actif", "Prix d'achat actif", "mdi:transmission-tower-import", "pricing", lambda d: d["prices"].get("active_buy"), "€/kWh"),
        FoxCatNumericSensor(c, "valeur_reinjection", "Valeur économique de la réinjection", "mdi:transmission-tower-export", "pricing", lambda d: d["prices"].get("export_value"), "€/kWh"),
        FoxCatNumericSensor(c, "cout_prelevement_instantane", "Coût instantané du prélèvement", "mdi:cash-minus", "pricing", lambda d: d["prices"].get("import_cost_rate_eur_h"), "€/h"),
        FoxCatNumericSensor(c, "valeur_reinjection_instantanee", "Valeur instantanée de la réinjection", "mdi:cash-plus", "pricing", lambda d: d["prices"].get("export_value_rate_eur_h"), "€/h"),
        FoxCatNumericSensor(c, "solde_reseau_instantane", "Solde financier instantané réseau", "mdi:scale-balance", "pricing", lambda d: d["prices"].get("net_cost_rate_eur_h"), "€/h"),
        FoxCatValueSensor(c, "derniere_trame", "Dernière trame énergétique", "mdi:clock-check-outline", "ems", lambda d: _iso(d["core"].get("last_frame"))),
        FoxCatValueSensor(c, "derniere_action", "Dernière action EMS", "mdi:clock-outline", "ems", lambda d: _iso(d["core"].get("last_action"))),
    ]
    async_add_entities(entities)


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else "Jamais"


class FoxCatValueSensor(FoxCatEntity, SensorEntity):
    def __init__(self, coordinator, key: str, name: str, icon: str, device: str, getter: Callable[[dict[str, Any]], Any]):
        super().__init__(coordinator, key, name, icon, device)
        self._getter = getter

    @property
    def native_value(self) -> Any:
        try:
            value = self._getter(self.coordinator.data)
            if value is None:
                return "Indisponible"
            return value
        except Exception:
            return "Indisponible"


class FoxCatNumericSensor(FoxCatEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, key: str, name: str, icon: str, device: str, getter: Callable[[dict[str, Any]], Any], unit: str | None = None, device_class=None):
        super().__init__(coordinator, key, name, icon, device)
        self._getter = getter
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if unit in {PERCENTAGE, "€/kWh"} or unit is None:
            self._attr_state_class = None

    @property
    def native_value(self) -> float | int | None:
        try:
            value = self._getter(self.coordinator.data)
            if value is None:
                return None
            if isinstance(value, int):
                return value
            return round(float(value), 4)
        except (TypeError, ValueError, KeyError, AttributeError):
            return None
