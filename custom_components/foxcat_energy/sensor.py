from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature, UnitOfEnergy
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
        FoxCatValueSensor(c, "boiler_user_status", "Boiler • Statut demande utilisateur", "mdi:hand-back-right-outline", "boiler", lambda d: d["core"].get("boiler_user_status", "AUCUNE")),
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
        FoxCatNumericSensor(c, "consommation_maison_calculee", "Consommation maison calculée par FoxCat", "mdi:home-lightning-bolt-outline", "ems", lambda d: d["measurements"].get("house_calculated_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "ecart_consommation_maison", "Écart consommation maison / bilan FoxCat", "mdi:delta", "ems", lambda d: d["measurements"].get("house_delta_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatValueSensor(c, "qualite_mesures", "Qualité des mesures FoxCat", "mdi:database-check-outline", "ems", lambda d: d["measurements"].get("quality", "INCONNUE")),
        FoxCatValueSensor(c, "materiel_onduleur_installe", "Matériel • Onduleur installé", "mdi:solar-power-variant", "hardware", lambda d: f"{d['settings'].get('hardware_inverter_brand', 'SolarEdge')} — {d['settings'].get('hardware_inverter_model', 'SE4K')}"),
        FoxCatValueSensor(c, "materiel_mesure_principale", "Matériel • Mesure réseau principale", "mdi:meter-electric-outline", "hardware", lambda d: f"{d['settings'].get('hardware_meter_brand', 'Smappee')} — {d['settings'].get('hardware_meter_model', 'Infinity')}"),
        FoxCatValueSensor(c, "source_production_pv", "Source production PV FoxCat", "mdi:source-branch", "ems", lambda d: d["measurements"].get("pv_source", "AUCUNE")),
        FoxCatValueSensor(c, "source_consommation_maison", "Source consommation maison FoxCat", "mdi:source-branch", "ems", lambda d: d["measurements"].get("house_source", "AUCUNE")),
        FoxCatValueSensor(c, "source_reinjection_reseau", "Source réinjection réseau FoxCat", "mdi:source-branch", "ems", lambda d: d["measurements"].get("grid_export_source", "AUCUNE")),
        FoxCatValueSensor(c, "source_prelevement_reseau", "Source prélèvement réseau FoxCat", "mdi:source-branch", "ems", lambda d: d["measurements"].get("grid_import_source", "AUCUNE")),
        FoxCatNumericSensor(c, "pri_compteur_trames_capteurs", "PRI • Publications capteurs traitées", "mdi:counter", "pri", lambda d: d["measurements"].get("pri_report_count", 0)),
        FoxCatValueSensor(c, "pri_derniere_source_trame", "PRI • Dernière source de trame", "mdi:access-point-network", "pri", lambda d: d["measurements"].get("last_pri_report_entity") or "AUCUNE"),
        FoxCatValueSensor(c, "pri_derniere_publication_capteur", "PRI • Dernière publication capteur", "mdi:clock-check-outline", "pri", lambda d: _iso(d["measurements"].get("last_pri_report_at"))),
        FoxCatValueSensor(c, "metronome_statut", "Statut métronome réseau", "mdi:metronome", "ems", lambda d: d["metronome"].get("status")),
        FoxCatValueSensor(c, "metronome_source", "Source métronome réseau", "mdi:source-branch-sync", "ems", lambda d: d["metronome"].get("source")),
        FoxCatValueSensor(c, "metronome_capteur_actif", "Capteur actif du métronome", "mdi:access-point-network", "ems", lambda d: d["metronome"].get("primary_entity") if d["metronome"].get("source") == "PRINCIPAL" else d["metronome"].get("fallback_entity")),
        FoxCatValueSensor(c, "metronome_dernier_battement", "Dernier battement métronome", "mdi:clock-check-outline", "ems", lambda d: _iso(d["metronome"].get("last_pulse_at"))),
        FoxCatNumericSensor(c, "metronome_compteur", "Compteur de battements métronome", "mdi:counter", "ems", lambda d: d["metronome"].get("pulse_count")),
        FoxCatNumericSensor(c, "metronome_periode", "Période du métronome réseau", "mdi:timer-sync-outline", "ems", lambda d: d["metronome"].get("period_s"), "s"),
        FoxCatValueSensor(c, "metronome_raison", "Diagnostic métronome réseau", "mdi:information-outline", "ems", lambda d: d["metronome"].get("last_reason")),
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
        FoxCatValueSensor(c, "pri_souverainete", "PRI • État de souveraineté", "mdi:shield-check-outline", "pri", lambda d: d["pri"].get("guard_reason", "INCONNU")),
        FoxCatNumericSensor(c, "pri_numero_trame", "PRI • Numéro de trame", "mdi:counter", "pri", lambda d: d["pri"].get("frame_id", 0)),
        FoxCatNumericSensor(c, "pri_score_actuel", "Score PRI actuel", "mdi:scale-balance", "pri", lambda d: d["pri"]["score_current"]),
        FoxCatNumericSensor(c, "pri_score_cible", "Score PRI cible", "mdi:scale-balance", "pri", lambda d: d["pri"]["score_target"]),
        FoxCatNumericSensor(c, "pri_cible_maison", "Repère PRI selon consommation (diagnostic)", "mdi:home-percent-outline", "pri", lambda d: d["pri"]["house_target_level"], PERCENTAGE),
        FoxCatNumericSensor(c, "pri_charge_reseau_estimee", "Charge maison estimée par bilan réseau", "mdi:home-lightning-bolt-outline", "pri", lambda d: d["pri"].get("estimated_house_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "pri_puissance_pv_cible", "Puissance PV cible PRI", "mdi:solar-power", "pri", lambda d: d["pri"].get("target_pv_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "pri_import_prevu", "Import réseau prévu au palier cible", "mdi:transmission-tower-import", "pri", lambda d: d["pri"].get("predicted_import_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
        FoxCatNumericSensor(c, "pri_export_prevu", "Réinjection prévue au palier cible", "mdi:transmission-tower-export", "pri", lambda d: d["pri"].get("predicted_export_w"), UnitOfPower.WATT, SensorDeviceClass.POWER),
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
        FoxCatNumericSensor(c, "bilan_conso_jour", "🏠 Maison • Consommation aujourd’hui", "mdi:home-lightning-bolt", "accounting", lambda d: d["accounting"]["today"]["house_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_pv_jour", "☀️ PV • Production aujourd’hui", "mdi:solar-power", "accounting", lambda d: d["accounting"]["today"]["pv_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_autoconso_jour", "☀️ PV • Énergie autoconsommée aujourd’hui", "mdi:home-import-outline", "accounting", lambda d: d["accounting"]["today"]["self_consumed_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_import_jour", "🏠 Maison • Prélèvement réseau aujourd’hui", "mdi:transmission-tower-import", "accounting", lambda d: d["accounting"]["today"]["import_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_export_jour", "☀️ PV • Réinjection aujourd’hui", "mdi:transmission-tower-export", "accounting", lambda d: d["accounting"]["today"]["export_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_autoconsommation_jour", "☀️ PV • Taux d’autoconsommation aujourd’hui", "mdi:percent-circle-outline", "accounting", lambda d: d["accounting"]["today"]["autoconsumption_pct"], PERCENTAGE),
        FoxCatNumericSensor(c, "bilan_autonomie_jour", "🏠 Maison • Taux d’autonomie aujourd’hui", "mdi:home-percent-outline", "accounting", lambda d: d["accounting"]["today"]["autonomy_pct"], PERCENTAGE),
        FoxCatNumericSensor(c, "bilan_cout_reseau_jour", "🏠 Maison • Coût réseau aujourd’hui", "mdi:cash-minus", "accounting", lambda d: d["accounting"]["today"]["import_cost_eur"], "€"),
        FoxCatNumericSensor(c, "bilan_valeur_injection_jour", "☀️ PV • Valeur réinjection aujourd’hui", "mdi:cash-plus", "accounting", lambda d: d["accounting"]["today"]["export_value_eur"], "€"),
        FoxCatNumericSensor(c, "bilan_cout_net_jour", "🏠 Maison • Coût net aujourd’hui", "mdi:cash-sync", "accounting", lambda d: d["accounting"]["today"]["net_grid_cost_eur"], "€"),
        FoxCatNumericSensor(c, "bilan_gain_solaire_jour", "☀️ PV • Gain solaire estimé aujourd’hui", "mdi:solar-power-variant", "accounting", lambda d: d["accounting"]["today"]["solar_gain_eur"], "€"),
        FoxCatNumericSensor(c, "bilan_conso_mois", "🏠 Maison • Consommation ce mois", "mdi:calendar-month", "accounting", lambda d: d["accounting"]["month"]["house_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_pv_mois", "☀️ PV • Production ce mois", "mdi:calendar-month-outline", "accounting", lambda d: d["accounting"]["month"]["pv_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_cout_net_mois", "🏠 Maison • Coût net ce mois", "mdi:cash-multiple", "accounting", lambda d: d["accounting"]["month"]["net_grid_cost_eur"], "€"),
        FoxCatNumericSensor(c, "bilan_conso_annee", "🏠 Maison • Consommation cette année", "mdi:calendar", "accounting", lambda d: d["accounting"]["year"]["house_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_pv_annee", "☀️ PV • Production cette année", "mdi:calendar-sun", "accounting", lambda d: d["accounting"]["year"]["pv_kwh"], UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        FoxCatNumericSensor(c, "bilan_cout_net_annee", "🏠 Maison • Coût net cette année", "mdi:cash-check", "accounting", lambda d: d["accounting"]["year"]["net_grid_cost_eur"], "€"),
        FoxCatValueSensor(c, "derniere_trame", "Dernière trame énergétique", "mdi:clock-check-outline", "ems", lambda d: _iso(d["core"].get("last_frame"))),
        FoxCatValueSensor(c, "derniere_action", "Dernière action EMS", "mdi:clock-outline", "ems", lambda d: _iso(d["core"].get("last_action"))),
    ]
    entities.extend([
        FoxCatValueSensor(c, "periode_tarifaire", "Période tarifaire", "mdi:clock-outline", "pricing", lambda d: d["prices"].get("period", "—")),
        FoxCatValueSensor(c, "politique_reseau_active", "Politique réseau active", "mdi:transmission-tower", "pricing", lambda d: d["settings"].get("network_policy", "Compensation")),
        FoxCatValueSensor(c, "ems_onduleur_etat", "EMS Onduleur • État", "mdi:solar-power-variant", "pri", lambda d: d["energy_bus"]["inverter"].get("status", "—")),
        FoxCatNumericSensor(c, "ems_onduleur_plafond_pv", "EMS Onduleur • Plafond PV", "mdi:solar-power", "pri", lambda d: d["energy_bus"]["inverter"].get("pv_limit_w", 0.0), "W"),
        FoxCatNumericSensor(c, "ems_onduleur_utilisation_plafond", "EMS Onduleur • Utilisation plafond", "mdi:gauge", "pri", lambda d: d["energy_bus"]["inverter"].get("pv_ratio_pct", 0.0), PERCENTAGE),
        FoxCatValueSensor(c, "ems_onduleur_potentiel", "EMS Onduleur • Potentiel solaire", "mdi:weather-sunny-alert", "pri", lambda d: "PLUS POSSIBLE" if d["energy_bus"]["inverter"].get("more_solar_possible") else ("MAX SOLAIRE ATTEINT" if d["energy_bus"]["inverter"].get("max_solar_reached") else "STABLE")),
    ])

    # Un jeu de capteurs est créé automatiquement pour chaque appareil FoxCat mesuré.
    appliance_defs = [("boiler", "Chauffe-eau")] + [(m.machine_id, m.name) for m in c.machines if m.power_sensor]
    for appliance_id, appliance_name in appliance_defs:
        safe = appliance_id.replace(" ", "_").lower()
        entities.extend([
            FoxCatNumericSensor(c, f"appareil_{safe}_energie_jour", f"🔌 {appliance_name} • Énergie aujourd’hui", "mdi:counter", "accounting", lambda d, aid=appliance_id: d["accounting"]["today"]["appliances"].get(aid,{}).get("energy_kwh",0.0), UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
            FoxCatNumericSensor(c, f"appareil_{safe}_solaire_jour", f"🔌 {appliance_name} • Part solaire aujourd’hui", "mdi:white-balance-sunny", "accounting", lambda d, aid=appliance_id: d["accounting"]["today"]["appliances"].get(aid,{}).get("solar_kwh",0.0), UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
            FoxCatNumericSensor(c, f"appareil_{safe}_reseau_jour", f"🔌 {appliance_name} • Part réseau aujourd’hui", "mdi:transmission-tower-import", "accounting", lambda d, aid=appliance_id: d["accounting"]["today"]["appliances"].get(aid,{}).get("grid_kwh",0.0), UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
            FoxCatNumericSensor(c, f"appareil_{safe}_cout_jour", f"🔌 {appliance_name} • Coût aujourd’hui", "mdi:cash", "accounting", lambda d, aid=appliance_id: d["accounting"]["today"]["appliances"].get(aid,{}).get("cost_eur",0.0), "€"),
            FoxCatNumericSensor(c, f"appareil_{safe}_hp_jour", f"🔌 {appliance_name} • Consommation HP aujourd’hui", "mdi:weather-sunny", "accounting", lambda d, aid=appliance_id: d["accounting"]["today"]["appliances"].get(aid,{}).get("hp_kwh",0.0), UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
            FoxCatNumericSensor(c, f"appareil_{safe}_hc_jour", f"🔌 {appliance_name} • Consommation HC aujourd’hui", "mdi:weather-night", "accounting", lambda d, aid=appliance_id: d["accounting"]["today"]["appliances"].get(aid,{}).get("hc_kwh",0.0), UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
            FoxCatValueSensor(c, f"appareil_{safe}_tarif_actuel", f"🔌 {appliance_name} • Tarif actuel", "mdi:clock-check-outline", "accounting", lambda d: d["prices"].get("period","—")),
        ])
    # FoxCat 1.4.2 — un seul appareil Home Assistant pour toute la comptabilité.
    # Les sections sont obtenues par une nomenclature stable des entités.
    for entity in entities:
        key = getattr(entity, "_foxcat_key", None) or getattr(entity, "_attr_unique_id", "")
        text = str(key).lower()

        if (
            text.startswith("bilan_")
            or "appareil_" in text
        ) and isinstance(entity, FoxCatNumericSensor):
            entity._foxcat_device_identifier = f"{c.entry.entry_id}_accounting"
            entity._foxcat_device_name = "FoxCat Energy – Coûts & Bilan"

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

    def __init__(self, coordinator, key: str, name: str, icon: str, device: str, getter: Callable[[dict[str, Any]], Any], unit: str | None = None, device_class=None, state_class=None, device_name: str | None = None, device_identifier: str | None = None):
        super().__init__(coordinator, key, name, icon, device)
        self._getter = getter
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._foxcat_device_name = device_name
        self._foxcat_device_identifier = device_identifier
        if state_class is not None:
            self._attr_state_class = state_class
        elif unit in {PERCENTAGE, "€/kWh", "€"} or unit is None:
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

    @property
    def device_info(self):
        if self._foxcat_device_identifier:
            return {
                "identifiers": {(DOMAIN, self._foxcat_device_identifier)},
                "name": self._foxcat_device_name or self._foxcat_device_identifier,
                "manufacturer": "FoxCat Energy",
                "model": "Coûts & Bilan",
                "via_device": (DOMAIN, self.coordinator.entry.entry_id),
            }
        return super().device_info

