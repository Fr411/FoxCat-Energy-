from __future__ import annotations

DOMAIN = "foxcat_energy"
VERSION = "1.3.1"
PLATFORMS = ["sensor", "binary_sensor", "switch", "select", "number", "button"]

# Configuration keys
CONF_INSTALLATION_NAME = "installation_name"
CONF_PV_SENSOR = "pv_sensor"
CONF_HOUSE_SENSOR = "house_sensor"
CONF_GRID_EXPORT_SENSOR = "grid_export_sensor"
CONF_GRID_IMPORT_SENSOR = "grid_import_sensor"
CONF_GRID_LEGACY_SENSOR = "grid_legacy_sensor"
CONF_BOILER_CLIMATE = "boiler_climate"
CONF_BOILER_TEMP_SENSOR = "boiler_temp_sensor"
CONF_BOILER_POWER_SENSOR = "boiler_power_sensor"
CONF_BOILER_BINARY = "boiler_binary"
CONF_PRI_L1 = "pri_l1"
CONF_PRI_L2 = "pri_l2"
CONF_PRI_L3 = "pri_l3"
CONF_PRI_L4 = "pri_l4"
CONF_WASHER_SOCKET = "washer_socket"
CONF_DRYER_SOCKET = "dryer_socket"
CONF_DISHWASHER_SOCKET = "dishwasher_socket"
CONF_WASHER_CYCLE = "washer_cycle"
CONF_DRYER_CYCLE = "dryer_cycle"
CONF_DISHWASHER_CYCLE = "dishwasher_cycle"

# V1.3: liste extensible des machines ON/OFF.
CONF_MACHINES_V13 = "machines_v13"

# Plages horaires configurables des prises machines. Deux fenêtres par machine
# permettent de conserver le comportement historique 21:30-07:00 et 10:30-17:00.
CONF_WASHER_ON_1 = "washer_on_1"
CONF_WASHER_OFF_1 = "washer_off_1"
CONF_WASHER_ON_2 = "washer_on_2"
CONF_WASHER_OFF_2 = "washer_off_2"
CONF_DRYER_ON_1 = "dryer_on_1"
CONF_DRYER_OFF_1 = "dryer_off_1"
CONF_DRYER_ON_2 = "dryer_on_2"
CONF_DRYER_OFF_2 = "dryer_off_2"
CONF_DISHWASHER_ON_1 = "dishwasher_on_1"
CONF_DISHWASHER_OFF_1 = "dishwasher_off_1"
CONF_DISHWASHER_ON_2 = "dishwasher_on_2"
CONF_DISHWASHER_OFF_2 = "dishwasher_off_2"

CONF_PRICE_CURRENT = "price_current"
CONF_PRICE_NEXT = "price_next"
CONF_PRICE_INJECTION = "price_injection"
CONF_PRICE_MIN_TODAY = "price_min_today"
CONF_PRICE_MAX_TODAY = "price_max_today"
CONF_PRICE_AVG_TODAY = "price_avg_today"
CONF_PRICE_MIN_TOMORROW = "price_min_tomorrow"
CONF_PRICE_MAX_TOMORROW = "price_max_tomorrow"
CONF_PRICE_AVG_TOMORROW = "price_avg_tomorrow"
CONF_PRICE_TOMORROW_AVAILABLE = "price_tomorrow_available"

# Configuration des plages tarifaires fixes / compensation.
CONF_TARIFF_HP_START_1 = "tariff_hp_start_1"
CONF_TARIFF_HP_END_1 = "tariff_hp_end_1"
CONF_TARIFF_HP_START_2 = "tariff_hp_start_2"
CONF_TARIFF_HP_END_2 = "tariff_hp_end_2"
CONF_TARIFF_HP_PRICE = "tariff_hp_price_eur_kwh"
CONF_TARIFF_HC_PRICE = "tariff_hc_price_eur_kwh"
CONF_TARIFF_FIXED_INJECTION_PRICE = "tariff_fixed_injection_eur_kwh"
CONF_TARIFF_HP_PRICE_SENSOR = "tariff_hp_price_sensor"
CONF_TARIFF_HC_PRICE_SENSOR = "tariff_hc_price_sensor"
CONF_TARIFF_FIXED_INJECTION_PRICE_SENSOR = "tariff_fixed_injection_price_sensor"

CONF_AI_TASK = "ai_task"
CONF_FORECAST_NOW = "forecast_now"
CONF_FORECAST_THIS_HOUR = "forecast_this_hour"
CONF_FORECAST_NEXT_HOUR = "forecast_next_hour"
CONF_FORECAST_TODAY = "forecast_today"
CONF_FORECAST_REMAINING_TODAY = "forecast_remaining_today"
CONF_FORECAST_1H = "forecast_1h"
CONF_FORECAST_12H = "forecast_12h"
CONF_FORECAST_24H = "forecast_24h"
CONF_FORECAST_PEAK_TODAY = "forecast_peak_today"
CONF_FORECAST_TOMORROW = "forecast_tomorrow"
CONF_FORECAST_PEAK_TOMORROW = "forecast_peak_tomorrow"

MODE_ECO = "Économie énergie"
MODE_ZERO = "Zéro injection"
MODE_ECS = "ECS solaire"
MODE_DYNAMIC = "Prix dynamique"
MODE_MANUAL = "Manuel"
MODES = [MODE_ECO, MODE_ZERO, MODE_ECS, MODE_DYNAMIC, MODE_MANUAL]

TARIFF_DYNAMIC = "Dynamique"
TARIFF_COMPENSATION = "Compensation"
TARIFF_TOU = "Bi-horaire HP/HC"
TARIFF_REGIMES = [TARIFF_DYNAMIC, TARIFF_COMPENSATION, TARIFF_TOU]
MODE_ALIASES = {
    "Economie énergie": MODE_ECO,
    "Économie énergie": MODE_ECO,
    "Zéro injection": MODE_ZERO,
    "Réinjection refusée": MODE_ZERO,
    "ECS solaire": MODE_ECS,
    "Prix dynamique": MODE_DYNAMIC,
    "Tarification dynamique": MODE_DYNAMIC,
    # Migration volontaire : le mode Confort disparaît en V1.2.0.
    # Un ancien réglage Confort est ramené en Manuel pour ne déclencher
    # aucune stratégie automatique sans choix explicite de l'utilisateur.
    "Confort": MODE_MANUAL,
    "Manuel": MODE_MANUAL,
    "Maxi solaire": MODE_ECS,
    "Réinjection autorisée": MODE_ECO,
}

BOILER_NONE = "AUCUNE"
BOILER_HEAT_45 = "CHAUFFE_45"
BOILER_BOOST_65 = "BOOST_65"
BOILER_STOP = "ARRET"

PHASE_ACQUISITION = "ACQUISITION"
PHASE_DECISION = "DECISION"
PHASE_WAIT_ACK = "WAIT_ACK"
ACK_IDLE = "IDLE"
ACK_WAIT = "WAIT"
ACK_OK = "OK"
ACK_NOK = "NOK"

# RRCR code is L4 L3 L2 L1.
RRCR_LEVEL_TO_CODE = {
    100: "0000",
    90: "1001",
    80: "1000",
    70: "0111",
    60: "0110",
    50: "0101",
    40: "0100",
    30: "0011",
    20: "0010",
    10: "0001",
    0: "1010",
}
RRCR_CODE_TO_LEVEL = {v: k for k, v in RRCR_LEVEL_TO_CODE.items()}

# Defaults intentionally mirror the supplied EMS automations where values were explicit.
DEFAULT_SETTINGS: dict[str, object] = {
    "regulation_active": False,
    "mode": MODE_ECO,
    "boiler_enabled": True,
    "boiler_allow_hc": True,
    "pri_enabled": True,
    "agressivite_ecs": False,
    "washer_enabled": True,
    "dryer_enabled": True,
    "dishwasher_enabled": True,
    "solar_advisor_enabled": True,
    "dynamic_negative_price_charge_enabled": True,
    "high_load_shed_enabled": False,
    "tariff_regime": TARIFF_COMPENSATION,
    "tariff_hp_price_eur_kwh": 0.0,
    "tariff_hc_price_eur_kwh": 0.0,
    "tariff_fixed_injection_eur_kwh": 0.0,
    "tariff_hp_start_1": "07:00:00",
    "tariff_hp_end_1": "11:00:00",
    "tariff_hp_start_2": "17:00:00",
    "tariff_hp_end_2": "22:00:00",
    "boiler_power_w": 1800.0,
    "boiler_temp_start_c": 43.0,
    "boiler_temp_normal_c": 45.0,
    "boiler_temp_boost_c": 65.0,
    "boiler_temp_safety_c": 68.0,
    "boiler_cycle_min_s": 120.0,
    "ack_tolerance_w": 400.0,
    "stability_tolerance_w": 500.0,
    "watchdog_timeout_s": 120.0,
    "inverter_power_w": 4000.0,
    "pri_step_percent": 10.0,
    "pri_pi_dt_s": 30.0,
    "pri_pi_target_export_w": 75.0,
    "pri_pi_kp": 0.012,
    "pri_pi_ki": 0.00010,
    "pri_pi_integral_limit_ws": 120000.0,
    "pri_pi_deadband_w": 100.0,
    "pri_pv_compare_tolerance_w": 200.0,
    "pri_probe_margin_w": 250.0,
    "pri_step_w": 400.0,
    "pri_weight_import": 1.0,
    "pri_weight_export": 2.0,
    "pri_export_optimal_w": 50.0,
    "pri_import_optimal_w": 100.0,
    "pri_export_acceptable_w": 150.0,
    "pri_import_acceptable_w": 200.0,
    "pri_score_margin": 25.0,
    "pri_inverter_ack_tolerance_w": 180.0,
    "pri_up_ack_delta_w": 100.0,
    "pri_grid_ack_delta_w": 50.0,
    "pri_export_threshold_dynamic_w": 800.0,
    "pri_import_threshold_dynamic_w": 500.0,
    "pri_pv_minimum_w": 200.0,
    "pri_end_solar_w": 5.0,
    "pri_end_solar_confirm_s": 180.0,
    "coverage_solar_min_percent": 80.0,
    "import_boiler_max_w": 1200.0,
    "surplus_pv_min_agressivite_w": 300.0,
    "autoconsommation_cible_percent": 95.0,
    "autoconsommation_min_percent": 85.0,
    "solar_threshold_min_w": 1300.0,
    "solar_threshold_possible_w": 1800.0,
    "solar_threshold_good_w": 2200.0,
    "solar_threshold_strong_w": 3000.0,
    "solar_confidence_min_percent": 70.0,
    "solar_window_min_minutes": 30.0,
    "dynamic_price_significant_delta": 0.01,
    "dynamic_injection_lucrative_threshold": -0.0001,
    "dynamic_grid_charge_threshold_eur_kwh": 0.0,
    "pri_boiler_settle_s": 30.0,
    "high_load_trigger_w": 5000.0,
    "high_load_release_w": 3500.0,
    "high_load_confirm_s": 30.0,
    "high_load_restore_s": 120.0,
}

NUMBER_DEFINITIONS = {
    "boiler_power_w": ("Puissance chauffe-eau", 100, 10000, 50, "W", "mdi:water-boiler"),
    "boiler_temp_start_c": ("Température reprise boiler", 30, 60, 0.5, "°C", "mdi:thermometer-chevron-down"),
    "boiler_temp_normal_c": ("Température confort boiler", 35, 65, 0.5, "°C", "mdi:thermometer"),
    "boiler_temp_boost_c": ("Température boost solaire", 45, 70, 0.5, "°C", "mdi:thermometer-plus"),
    "boiler_temp_safety_c": ("Sécurité température boiler", 50, 80, 0.5, "°C", "mdi:thermometer-alert"),
    "boiler_cycle_min_s": ("Cycle minimum boiler", 30, 600, 10, "s", "mdi:timer-lock"),
    "ack_tolerance_w": ("Tolérance ACK", 50, 3000, 50, "W", "mdi:check-decagram-outline"),
    "stability_tolerance_w": ("Tolérance stabilité T0/T1", 50, 3000, 50, "W", "mdi:chart-bell-curve-cumulative"),
    "watchdog_timeout_s": ("Délai watchdog trame", 30, 600, 10, "s", "mdi:timer-alert-outline"),
    "inverter_power_w": ("Puissance nominale onduleur", 500, 30000, 100, "W", "mdi:solar-power"),
    "pri_step_w": ("Pas de puissance PRI", 100, 1000, 100, "W", "mdi:stairs"),
    "pri_pi_target_export_w": ("Consigne export PRI-PI", 0, 500, 10, "W", "mdi:target"),
    "pri_pi_kp": ("Gain proportionnel PRI-PI", 0.001, 0.1, 0.001, None, "mdi:chart-bell-curve"),
    "pri_pi_ki": ("Gain intégral PRI-PI", 0.00001, 0.005, 0.00001, None, "mdi:chart-timeline-variant"),
    "pri_pv_compare_tolerance_w": ("Tolérance comparateur PRI/PV", 50, 500, 10, "W", "mdi:compare"),
    "pri_probe_margin_w": ("Marge sondage solaire boiler", 0, 800, 50, "W", "mdi:solar-power"),
    "pri_weight_import": ("Poids import PRI", 0.1, 10, 0.1, None, "mdi:scale-balance"),
    "pri_weight_export": ("Poids réinjection PRI", 0.1, 10, 0.1, None, "mdi:scale-balance"),
    "pri_export_optimal_w": ("Réinjection idéale maximale", 0, 1000, 10, "W", "mdi:transmission-tower-export"),
    "pri_import_optimal_w": ("Prélèvement idéal maximal", 0, 1000, 10, "W", "mdi:transmission-tower-import"),
    "pri_export_acceptable_w": ("Réinjection acceptable", 0, 3000, 10, "W", "mdi:transmission-tower-export"),
    "pri_import_acceptable_w": ("Prélèvement acceptable", 0, 3000, 10, "W", "mdi:transmission-tower-import"),
    "pri_score_margin": ("Marge de score PRI", 0, 500, 5, None, "mdi:delta"),
    "pri_inverter_ack_tolerance_w": ("Tolérance ACK onduleur", 0, 1000, 10, "W", "mdi:check-network-outline"),
    "pri_up_ack_delta_w": ("Delta ACK remontée PRI", 0, 1000, 10, "W", "mdi:arrow-up-bold"),
    "pri_grid_ack_delta_w": ("Delta ACK réseau PRI", 0, 1000, 10, "W", "mdi:transmission-tower"),
    "pri_export_threshold_dynamic_w": ("Seuil réduction PRI dynamique", 0, 5000, 50, "W", "mdi:arrow-down-bold"),
    "pri_import_threshold_dynamic_w": ("Seuil remontée PRI dynamique", 0, 5000, 50, "W", "mdi:arrow-up-bold"),
    "pri_pv_minimum_w": ("Puissance de production PV minimale pour le PRI", 0, 1000, 10, "W", "mdi:solar-power-variant"),
    "pri_end_solar_w": ("Seuil fin solaire", 0, 100, 1, "W", "mdi:weather-sunset"),
    "pri_end_solar_confirm_s": ("Confirmation fin solaire", 30, 900, 10, "s", "mdi:timer-sand"),
    "coverage_solar_min_percent": ("Couverture solaire minimale ECS", 0, 100, 1, "%", "mdi:percent-circle-outline"),
    "import_boiler_max_w": ("Puissance prélevée maximale pour le chauffe-eau", 0, 3000, 50, "W", "mdi:transmission-tower-import"),
    "surplus_pv_min_agressivite_w": ("Surplus PV minimum agressivité", 0, 3000, 50, "W", "mdi:solar-power-variant-outline"),
    "autoconsommation_cible_percent": ("Autoconsommation cible", 0, 100, 1, "%", "mdi:home-lightning-bolt-outline"),
    "autoconsommation_min_percent": ("Autoconsommation minimale", 0, 100, 1, "%", "mdi:home-lightning-bolt"),
    "solar_threshold_min_w": ("Solaire seuil minimum", 0, 6000, 100, "W", "mdi:white-balance-sunny"),
    "solar_threshold_possible_w": ("Solaire fenêtre possible", 0, 6000, 100, "W", "mdi:white-balance-sunny"),
    "solar_threshold_good_w": ("Solaire bonne fenêtre", 0, 6000, 100, "W", "mdi:white-balance-sunny"),
    "solar_threshold_strong_w": ("Solaire forte fenêtre", 0, 6000, 100, "W", "mdi:white-balance-sunny"),
    "solar_confidence_min_percent": ("Confiance solaire minimale", 0, 100, 1, "%", "mdi:weather-sunny-alert"),
    "solar_window_min_minutes": ("Durée minimale fenêtre solaire", 5, 240, 5, "min", "mdi:timeline-clock-outline"),
    "dynamic_price_significant_delta": ("Écart de prix significatif", 0, 1, 0.001, "€/kWh", "mdi:cash-sync"),
    "dynamic_injection_lucrative_threshold": ("Seuil injection rémunératrice", -1, 1, 0.0001, "€/kWh", "mdi:cash-plus"),
    "dynamic_grid_charge_threshold_eur_kwh": ("Seuil charge réseau prix négatif", -1, 0, 0.001, "€/kWh", "mdi:transmission-tower-import"),
    "tariff_hp_price_eur_kwh": ("Prix achat heures pleines", 0, 2, 0.001, "€/kWh", "mdi:cash-clock"),
    "tariff_hc_price_eur_kwh": ("Prix achat heures creuses", 0, 2, 0.001, "€/kWh", "mdi:cash-clock"),
    "tariff_fixed_injection_eur_kwh": ("Prix fixe de réinjection", -1, 2, 0.001, "€/kWh", "mdi:cash-plus"),
    "pri_boiler_settle_s": ("Temporisation PRI après action boiler", 0, 180, 5, "s", "mdi:timer-sync-outline"),
    "high_load_trigger_w": ("Seuil haute consommation", 1000, 20000, 100, "W", "mdi:flash-alert"),
    "high_load_release_w": ("Seuil de réarmement après haute consommation", 500, 19000, 100, "W", "mdi:flash-check"),
    "high_load_confirm_s": ("Confirmation haute consommation", 0, 300, 5, "s", "mdi:timer-alert-outline"),
    "high_load_restore_s": ("Temporisation de réarmement du délestage", 0, 900, 10, "s", "mdi:timer-check-outline"),
}

SWITCH_DEFINITIONS = {
    "regulation_active": ("Régulation FoxCat active", "mdi:power"),
    "boiler_enabled": ("Boiler géré par FoxCat", "mdi:water-boiler"),
    "boiler_allow_hc": ("Boiler autorisé en heures creuses", "mdi:clock-check-outline"),
    "pri_enabled": ("Réduction de puissance onduleur", "mdi:solar-power-variant"),
    "agressivite_ecs": ("Agressivité ECS solaire", "mdi:water-boiler-auto"),
    "washer_enabled": ("Gestion lave-linge", "mdi:washing-machine"),
    "dryer_enabled": ("Gestion sèche-linge", "mdi:tumble-dryer"),
    "dishwasher_enabled": ("Gestion lave-vaisselle", "mdi:dishwasher"),
    "solar_advisor_enabled": ("Conseiller solaire EMS 2", "mdi:weather-sunny-alert"),
    "dynamic_negative_price_charge_enabled": ("Charge réseau si prix dynamique négatif", "mdi:transmission-tower-import"),
    "high_load_shed_enabled": ("Délestage haute consommation", "mdi:home-lightning-bolt-outline"),
}

# Legacy helpers are read only once at first setup to preserve the user's existing tuning.
LEGACY_SETTING_MAP = {
    "boiler_power_w": "input_number.ems_boiler_puissance",
    "boiler_temp_start_c": "input_number.ems_boiler_temp_start",
    "boiler_temp_normal_c": "input_number.ems_boiler_temp_normal",
    "boiler_temp_boost_c": "input_number.ems_boiler_temp_boost",
    "boiler_temp_safety_c": "input_number.ems_boiler_temp_securite",
    "boiler_cycle_min_s": "input_number.ems_boiler_cycle_min_secondes",
    "ack_tolerance_w": "input_number.ems_ack_tolerance",
    "stability_tolerance_w": "input_number.ems_stability_tolerance",
    "pri_export_threshold_dynamic_w": "input_number.ems_pri_export_threshold",
    "pri_import_threshold_dynamic_w": "input_number.ems_pri_import_threshold",
    "coverage_solar_min_percent": "input_number.ems_couverture_solaire_min_dynamique",
    "import_boiler_max_w": "input_number.ems_import_boiler_max_dynamique",
    "surplus_pv_min_agressivite_w": "input_number.ems_surplus_pv_min_agressivite",
    "autoconsommation_cible_percent": "input_number.ems_autoconsommation_cible",
    "autoconsommation_min_percent": "input_number.ems_autoconsommation_min",
    "solar_threshold_min_w": "input_number.ems_solaire_seuil_minimum",
    "solar_threshold_possible_w": "input_number.ems_solaire_seuil_possible",
    "solar_threshold_good_w": "input_number.ems_solaire_seuil_bon",
    "solar_threshold_strong_w": "input_number.ems_solaire_seuil_fort",
    "solar_confidence_min_percent": "input_number.ems_solaire_confiance_minimum",
    "solar_window_min_minutes": "input_number.ems_solaire_duree_minimum",
}
LEGACY_SWITCH_MAP = {
    "boiler_enabled": "input_boolean.ems_boiler",
    "boiler_allow_hc": "input_boolean.ems_boiler_allow_hc",
    "pri_enabled": "input_boolean.ems_pri",
    "agressivite_ecs": "input_boolean.ems_agressivite_active",
    "washer_enabled": "input_boolean.ems_lave_linge",
    "dryer_enabled": "input_boolean.ems_seche_linge",
    "dishwasher_enabled": "input_boolean.ems_lave_vaisselle",
}
LEGACY_MODE_ENTITY = "input_select.ems_mode"

KNOWN_LEGACY_AUTOMATIONS = [
    "automation.foxcat_mode_ecs_solaire_v1_strategie",
    "automation.foxcat_mode_economie_energie_v1_strategie",
    "automation.foxcat_mode_prix_dynamique_v1_strategie",
]
