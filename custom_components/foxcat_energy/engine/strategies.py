from __future__ import annotations

from datetime import datetime

from ..const import (
    BOILER_BOOST_65,
    BOILER_HEAT_45,
    BOILER_NONE,
    BOILER_STOP,
    MODE_COMFORT,
    MODE_DYNAMIC,
    MODE_ECO,
    MODE_ECS,
    MODE_MANUAL,
    MODE_ZERO,
)
from .models import BoilerIntent, EnergySnapshot, SolarForecast
from .tariff import is_offpeak, is_offpeak_day, is_offpeak_night, is_peak, minute_of_day


def _coverage(grid_net_w: float, boiler_power_w: float) -> float:
    if boiler_power_w <= 0:
        return 0.0
    return max(grid_net_w, 0.0) / boiler_power_w * 100.0


def _thermal_deadline(snapshot: EnergySnapshot, settings: dict[str, object], now: datetime) -> bool:
    normal = float(settings["boiler_temp_normal_c"])
    delta = max(normal - snapshot.boiler_temp_c, 0.0)
    heating_rate_c_h = 10.0
    margin_minutes = 30.0
    need_minutes = delta / heating_rate_c_h * 60.0 + margin_minutes
    m = minute_of_day(now)
    if m < 420:
        available = 420 - m
    elif m < 1020:
        available = 1020 - m
    else:
        available = (1440 - m) + 420
    return snapshot.boiler_temp_c < normal and available <= need_minutes


def _ecs_last_departure(snapshot: EnergySnapshot, settings: dict[str, object], now: datetime) -> bool:
    m = minute_of_day(now)
    if 0 <= m < 420:
        minutes_end = 420 - m
    elif 660 <= m < 1020:
        minutes_end = 1020 - m
    elif 1320 <= m < 1440:
        minutes_end = (1440 - m) + 420
    else:
        return False
    normal = float(settings["boiler_temp_normal_c"])
    projected_end = snapshot.boiler_temp_c - 0.5 * (minutes_end / 60.0)
    heating_minutes = max(0.0, (normal - projected_end) / 10.0 * 60.0)
    return minutes_end - heating_minutes - 30.0 <= 0


def evaluate_ecs_solar(
    snapshot: EnergySnapshot,
    t0: EnergySnapshot,
    settings: dict[str, object],
    now: datetime,
    boiler_on_seconds: float,
    current_demand: str,
) -> BoilerIntent:
    normal = float(settings["boiler_temp_normal_c"])
    boost = float(settings["boiler_temp_boost_c"])
    safety = float(settings["boiler_temp_safety_c"])
    cycle_min = float(settings["boiler_cycle_min_s"])
    boiler_power = float(settings["boiler_power_w"])

    if not bool(settings["boiler_enabled"]):
        return BoilerIntent(BOILER_STOP, "Boiler désactivé dans FoxCat.", "SECURITE")
    if snapshot.boiler_temp_c >= safety:
        return BoilerIntent(BOILER_STOP, "Sécurité thermique atteinte.", "SECURITE")
    if snapshot.machine_active:
        return BoilerIntent(BOILER_STOP, "Machine protégée en cycle : boiler libéré.", "MACHINE")
    if snapshot.boiler_temp_c >= boost:
        return BoilerIntent(BOILER_STOP, "65 °C atteint : stockage thermique terminé.", "TEMPERATURE")
    if is_peak(now) and snapshot.boiler_on and snapshot.import_w > 0:
        return BoilerIntent(BOILER_STOP, "HP : achat réseau détecté, arrêt demandé.", "HP")

    if snapshot.boiler_on and boiler_on_seconds < cycle_min:
        if snapshot.boiler_temp_c < normal:
            return BoilerIntent(BOILER_HEAT_45, "Cycle minimum actif : maintien CHAUFFE_45.", "CYCLE_MIN")
        if is_offpeak(now) and snapshot.boiler_temp_c < boost:
            return BoilerIntent(BOILER_BOOST_65, "45 °C atteint pendant le cycle minimum : transition BOOST_65 sans coupure.", "CYCLE_MIN")
        return BoilerIntent(BOILER_STOP, "Cycle minimum : aucune prolongation autorisée.", "CYCLE_MIN")

    coverage_now = _coverage(snapshot.grid_net_w, boiler_power)
    coverage_t0 = _coverage(t0.grid_net_w, boiler_power)
    last_departure = _ecs_last_departure(snapshot, settings, now)

    if is_offpeak_night(now):
        if not bool(settings["boiler_allow_hc"]):
            return BoilerIntent(BOILER_NONE, "Nuit HC : autorisation boiler HC désactivée.", "HC_NUIT")
        m = minute_of_day(now)
        if 1320 <= m < 1380:  # 22:00-23:00 observation
            if snapshot.boiler_temp_c < normal and last_departure:
                return BoilerIntent(BOILER_HEAT_45, "Nuit observation : failback atteint.", "ECS_HC_45")
            return BoilerIntent(BOILER_NONE, "22h00-23h00 : observation thermique.", "HC_NUIT")
        if 1380 <= m < 1400:  # 23:00-23:20
            if snapshot.boiler_temp_c < normal:
                return BoilerIntent(BOILER_HEAT_45, "23h00-23h20 : charge initiale nocturne.", "ECS_HC_45")
            return BoilerIntent(BOILER_STOP, "Charge initiale : 45 °C déjà atteint.", "HC_NUIT")
        if 1400 <= m < 1430:  # 23:20-23:50
            if snapshot.boiler_temp_c < normal and last_departure:
                return BoilerIntent(BOILER_HEAT_45, "Stabilisation : failback critique.", "ECS_HC_45")
            return BoilerIntent(BOILER_STOP, "23h20-23h50 : stabilisation de la sonde.", "HC_NUIT")
        if snapshot.boiler_on and snapshot.boiler_temp_c < normal:
            return BoilerIntent(BOILER_HEAT_45, "Failback nuit : chauffe engagée, continuité jusqu'à 45 °C.", "ECS_HC_45")
        if snapshot.boiler_temp_c < normal and last_departure:
            return BoilerIntent(BOILER_HEAT_45, "Failback nuit atteint : CHAUFFE_45.", "ECS_HC_45")
        if snapshot.boiler_temp_c >= normal:
            return BoilerIntent(BOILER_STOP, "Failback nuit : confort 45 °C assuré.", "HC_NUIT")
        return BoilerIntent(BOILER_NONE, "Nuit HC : aucune chauffe nécessaire.", "HC_NUIT")

    if is_offpeak_day(now):
        if not bool(settings["boiler_allow_hc"]):
            return BoilerIntent(BOILER_NONE, "HC jour : autorisation boiler HC désactivée.", "HC_JOUR")

        aggression = bool(settings["agressivite_ecs"])
        min_cov = float(settings["coverage_solar_min_percent"])
        surplus_min = float(settings["surplus_pv_min_agressivite_w"])
        import_max = float(settings["import_boiler_max_w"])
        coverage_depart = min(min_cov, 80.0) if aggression and snapshot.pv_w > 0 and snapshot.grid_net_w >= surplus_min else 80.0
        solar_only_boost = coverage_t0 >= 100 and coverage_now >= 100
        if solar_only_boost:
            boost_depart_ok = True
        elif aggression:
            boost_depart_ok = snapshot.pv_w > 0 and snapshot.grid_net_w >= surplus_min and coverage_t0 >= min_cov and coverage_now >= min_cov
        else:
            boost_depart_ok = snapshot.pv_w > 0 and t0.grid_net_w >= 600 and snapshot.grid_net_w >= 600
        allowed_import_boost = import_max if aggression and snapshot.pv_w > 0 else (1200.0 if snapshot.pv_w > 0 else 0.0)
        boost_continuation_ok = snapshot.pv_w > 0 and snapshot.import_w <= allowed_import_boost

        if snapshot.boiler_on and snapshot.boiler_temp_c < normal:
            return BoilerIntent(BOILER_HEAT_45, "HC jour : chauffe 45 °C engagée, continuité.", "ECS_HC_45")
        if snapshot.boiler_on and current_demand == BOILER_HEAT_45 and normal <= snapshot.boiler_temp_c < boost:
            if boost_continuation_ok:
                return BoilerIntent(BOILER_BOOST_65, "45 °C atteint : transition directe vers BOOST_65.", "ECS_BOOST_65")
            return BoilerIntent(BOILER_STOP, "45 °C atteint : boost non justifié.", "HC_JOUR")
        if snapshot.boiler_on and current_demand == BOILER_BOOST_65 and snapshot.boiler_temp_c < boost:
            if boost_continuation_ok:
                return BoilerIntent(BOILER_BOOST_65, "BOOST_65 maintenu : conditions PV/import acceptables.", "ECS_BOOST_65")
            return BoilerIntent(BOILER_STOP, "BOOST_65 arrêté : PV/import hors limite.", "HC_JOUR")
        if not snapshot.boiler_on and normal <= snapshot.boiler_temp_c < boost and boost_depart_ok:
            return BoilerIntent(BOILER_BOOST_65, "HC jour : opportunité de stockage solaire confirmée.", "ECS_BOOST_65")
        if not snapshot.boiler_on and snapshot.boiler_temp_c < normal and coverage_t0 >= coverage_depart and coverage_now >= coverage_depart:
            return BoilerIntent(BOILER_HEAT_45, "HC jour : couverture solaire stable suffisante.", "ECS_HC_45")
        if snapshot.boiler_temp_c < normal and last_departure:
            return BoilerIntent(BOILER_HEAT_45, "HC jour : failback atteint.", "ECS_HC_45")
        if 960 <= minute_of_day(now) < 1020 and snapshot.boiler_temp_c < normal:
            return BoilerIntent(BOILER_HEAT_45, "16h00-17h00 : rattrapage HC vers 45 °C.", "ECS_HC_45")
        return BoilerIntent(BOILER_NONE, "HC jour : attente, aucune chauffe nécessaire.", "HC_JOUR")

    # Hours pleines
    if snapshot.boiler_on and snapshot.boiler_temp_c < normal and snapshot.import_w <= 0:
        return BoilerIntent(BOILER_HEAT_45, "HP : chauffe 45 °C maintenue sans achat réseau.", "ECS_SOLAR_45")
    if not snapshot.boiler_on and snapshot.boiler_temp_c < normal and coverage_t0 >= 100 and coverage_now >= 100:
        return BoilerIntent(BOILER_HEAT_45, "HP : CHAUFFE_45 autorisée à 100 % solaire sur deux trames.", "ECS_SOLAR_45")
    if snapshot.boiler_on and snapshot.boiler_temp_c < normal and snapshot.import_w > 0:
        return BoilerIntent(BOILER_STOP, "HP : apparition d'un achat réseau.", "HP")
    if snapshot.boiler_temp_c >= normal:
        return BoilerIntent(BOILER_STOP, "HP : 45 °C atteint, aucun boost opportuniste.", "HP")
    return BoilerIntent(BOILER_NONE, "HP : aucune opportunité solaire exploitable.", "HP")


def evaluate_dynamic(
    snapshot: EnergySnapshot,
    t0: EnergySnapshot,
    settings: dict[str, object],
    now: datetime,
    prices: dict[str, float | None],
    solar: SolarForecast,
    boiler_absorbing: bool,
) -> BoilerIntent:
    if not bool(settings["boiler_enabled"]):
        return BoilerIntent(BOILER_STOP, "Boiler désactivé dans FoxCat.", "SECURITE")
    if snapshot.machine_active:
        return BoilerIntent(BOILER_STOP, "Cycle machine protégé. Boiler cède la priorité.", "MACHINE")
    if snapshot.boiler_temp_c >= float(settings["boiler_temp_safety_c"]):
        return BoilerIntent(BOILER_STOP, "Sécurité thermique boiler.", "SECURITE")

    current = prices.get("current")
    next_price = prices.get("next")
    pmin = prices.get("min_today")
    pmax = prices.get("max_today")
    avg = prices.get("avg_today")
    injection = prices.get("injection")
    if current is None or pmin is None or pmax is None:
        return BoilerIntent(BOILER_NONE, "Prix dynamiques invalides : régulation suspendue.", "PRIX")
    if next_price is None:
        next_price = current
    if avg is None:
        avg = current
    if injection is None:
        injection = 0.0

    normal = float(settings["boiler_temp_normal_c"])
    start = float(settings["boiler_temp_start_c"])
    boost = float(settings["boiler_temp_boost_c"])
    boiler_power = float(settings["boiler_power_w"])
    coverage_now = _coverage(snapshot.grid_net_w, boiler_power)
    coverage_t0 = _coverage(t0.grid_net_w, boiler_power)
    amplitude = max(pmax - pmin, 0.001)
    position = (current - pmin) / amplitude
    very_low = position <= 0.20 or current <= pmin + 0.005
    low = position <= 0.45 or current < avg
    very_high = position >= 0.80 or current >= pmax - 0.005
    significant = float(settings["dynamic_price_significant_delta"])
    injection_lucrative = injection < float(settings["dynamic_injection_lucrative_threshold"])
    boost_solar = normal <= snapshot.boiler_temp_c < boost and coverage_t0 >= 100 and coverage_now >= 100 and not injection_lucrative
    solar_future = solar.available and solar.confidence >= float(settings["solar_confidence_min_percent"]) and solar.potential in {"Moyen", "Bon", "Fort"}
    thermal_deadline = _thermal_deadline(snapshot, settings, now)

    if snapshot.boiler_temp_c >= normal and not boost_solar:
        return BoilerIntent(BOILER_STOP, "Température ECS normale atteinte.", "PRIX")
    if snapshot.boiler_temp_c < normal and coverage_t0 >= 100 and coverage_now >= 100:
        return BoilerIntent(BOILER_HEAT_45, "Solaire prioritaire pour le besoin ECS.", "DYNAMIC_SOLAR_45")
    if boost_solar:
        return BoilerIntent(BOILER_BOOST_65, "Stockage solaire ECS économiquement pertinent.", "DYNAMIC_BOOST_65")
    if snapshot.boiler_temp_c < normal and thermal_deadline:
        return BoilerIntent(BOILER_HEAT_45, "Dernier départ thermique sûr atteint.", "DYNAMIC_GARANTIE")
    if snapshot.boiler_temp_c < normal and very_low:
        return BoilerIntent(BOILER_HEAT_45, "Créneau tarifaire très favorable utilisé.", "PRIX")
    if snapshot.boiler_temp_c < normal and low and next_price >= current + significant:
        return BoilerIntent(BOILER_HEAT_45, "Bon prix actuel avant hausse.", "PRIX")
    if snapshot.boiler_temp_c < start and current <= avg and not very_high:
        return BoilerIntent(BOILER_HEAT_45, "Besoin ECS et tarif sous la moyenne.", "PRIX")
    if snapshot.boiler_temp_c < normal and next_price < current - significant and not thermal_deadline:
        return BoilerIntent(BOILER_STOP, "Attente d'un meilleur prix à l'heure suivante.", "PRIX")
    if snapshot.boiler_temp_c < normal and very_high:
        return BoilerIntent(BOILER_STOP, "Prix élevé évité.", "PRIX")
    if snapshot.boiler_temp_c < normal and solar_future and not thermal_deadline and not very_low:
        return BoilerIntent(BOILER_STOP, "Attente solaire autorisée par EMS 2.", "EMS2")
    return BoilerIntent(BOILER_NONE, "Surveillance dynamique : aucune action nécessaire.", "PRIX")


def evaluate_mode(
    mode: str,
    snapshot: EnergySnapshot,
    t0: EnergySnapshot,
    settings: dict[str, object],
    now: datetime,
    boiler_on_seconds: float,
    current_demand: str,
    prices: dict[str, float | None],
    solar: SolarForecast,
) -> BoilerIntent:
    normal = float(settings["boiler_temp_normal_c"])
    start = float(settings["boiler_temp_start_c"])

    if mode == MODE_MANUAL or mode == MODE_ZERO:
        return BoilerIntent(BOILER_NONE, "Aucune stratégie boiler automatique dans ce mode.", mode)

    if mode == MODE_COMFORT:
        # This mode was named in the supplied EMS but had no dedicated strategy file.
        # Safe completion: guarantee 45 °C, while all central machine/thermal safety rules remain sovereign.
        if snapshot.boiler_temp_c < start and not snapshot.machine_active:
            return BoilerIntent(BOILER_HEAT_45, "Mode Confort : maintien du confort ECS à 45 °C.", "CONFORT")
        if snapshot.boiler_temp_c >= normal and snapshot.boiler_on:
            return BoilerIntent(BOILER_STOP, "Mode Confort : température cible atteinte.", "CONFORT")
        return BoilerIntent(BOILER_NONE, "Mode Confort stable.", "CONFORT")

    if mode == MODE_ECO:
        if snapshot.boiler_on and snapshot.boiler_temp_c >= normal:
            return BoilerIntent(BOILER_STOP, "Économie énergie : température 45 °C atteinte.", "ECO")
        if is_peak(now) and snapshot.boiler_on and snapshot.import_w > 50:
            return BoilerIntent(BOILER_STOP, "Économie énergie : import HP interdit pour le boiler.", "ECO")
        if is_offpeak(now) and bool(settings["boiler_enabled"]) and bool(settings["boiler_allow_hc"]) and not snapshot.boiler_on and not snapshot.machine_active and snapshot.boiler_temp_c < start:
            return BoilerIntent(BOILER_HEAT_45, "Économie énergie : seuil HC atteint, chauffe à 45 °C.", "HC_RESEAU")
        return BoilerIntent(BOILER_NONE, "Économie énergie : aucune action boiler.", "ECO")

    if mode == MODE_ECS:
        return evaluate_ecs_solar(snapshot, t0, settings, now, boiler_on_seconds, current_demand)

    if mode == MODE_DYNAMIC:
        return evaluate_dynamic(snapshot, t0, settings, now, prices, solar, current_demand in {BOILER_HEAT_45, BOILER_BOOST_65})

    return BoilerIntent(BOILER_NONE, "Mode inconnu : aucune action.", "AUCUNE")
