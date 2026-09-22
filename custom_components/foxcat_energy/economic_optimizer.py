from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable

from .const import (
    NETWORK_POLICY_COMPENSATION,
    TARIFF_DYNAMIC,
    TARIFF_TOU,
)
from .engine.models import EnergySnapshot
from .engine.tariff import tariff_period


@dataclass(frozen=True)
class PricePoint:
    at: datetime
    price: float
    source: str = "UNKNOWN"


@dataclass(frozen=True)
class EconomicDecision:
    code: str
    label: str
    reason: str
    regime: str
    confidence: str
    flexible_start: bool
    prefer_self_consumption: bool
    prefer_export: bool
    current_buy_eur_kwh: float | None
    export_value_eur_kwh: float | None
    best_future_buy_eur_kwh: float | None
    best_future_at: datetime | None
    saving_vs_now_eur_kwh: float | None
    horizon_hours: int
    forecast_points: int
    application: str = "DEMARRAGES_AUTOMATIQUES_MACHINES"

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["best_future_at"] = self.best_future_at.isoformat() if self.best_future_at else None
        return data


_PRICE_KEYS = (
    "price", "value", "total", "price_eur_kwh", "eur_kwh", "eur_per_kwh",
    "import_price", "export_price", "marketprice", "prijs",
)
_TIME_KEYS = (
    "start", "datetime", "time", "timestamp", "starts_at", "start_time", "date", "hour",
)
_SERIES_KEYS = (
    "prices", "forecast", "hourly", "data", "values", "entries",
    "raw_today", "raw_tomorrow", "today", "tomorrow",
)


def _float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any, now: datetime) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        raw = float(value)
        if raw > 10_000_000_000:  # milliseconds
            raw /= 1000.0
        try:
            dt = datetime.fromtimestamp(raw, tz=now.tzinfo)
        except (ValueError, OSError, OverflowError):
            return None
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            # "14:00" / "14:00:00" means today in the HA timezone.
            try:
                parts = text.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                dt = now.replace(hour=hour % 24, minute=minute % 60, second=0, microsecond=0)
            except (ValueError, IndexError):
                return None
    else:
        return None
    if dt.tzinfo is None and now.tzinfo is not None:
        dt = dt.replace(tzinfo=now.tzinfo)
    return dt


def extract_price_points(raw: Any, now: datetime, *, source: str, horizon_hours: int = 36) -> list[PricePoint]:
    """Extract a generic future price series from common HA sensor attributes.

    The parser is intentionally tolerant: it understands lists of dictionaries,
    ``(timestamp, price)`` pairs and plain numeric hourly lists. It never imports
    a provider SDK, keeping FoxCat fully local and Python-only.
    """
    horizon_end = now + timedelta(hours=max(int(horizon_hours), 1))
    found: list[PricePoint] = []

    def add(at: datetime | None, price: float | None) -> None:
        if at is None or price is None:
            return
        # Keep a small look-back so the current slot can still be represented.
        if at < now - timedelta(hours=1) or at > horizon_end:
            return
        found.append(PricePoint(at=at, price=price, source=source))

    def walk(value: Any, base_at: datetime | None = None) -> None:
        if isinstance(value, dict):
            price = next((_float(value.get(key)) for key in _PRICE_KEYS if key in value and _float(value.get(key)) is not None), None)
            at = next((_parse_datetime(value.get(key), now) for key in _TIME_KEYS if key in value and _parse_datetime(value.get(key), now) is not None), None)
            if price is not None:
                add(at or base_at, price)
            for key in _SERIES_KEYS:
                if key in value:
                    series_base = base_at
                    if key in {"today", "raw_today"}:
                        series_base = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif key in {"tomorrow", "raw_tomorrow"}:
                        series_base = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    walk(value[key], series_base)
            return
        if isinstance(value, (list, tuple)):
            if len(value) == 2 and not isinstance(value[0], (list, tuple, dict)):
                at = _parse_datetime(value[0], now)
                price = _float(value[1])
                if at is not None and price is not None:
                    add(at, price)
                    return
            # Plain numeric lists are interpreted as hourly values starting at
            # the beginning of the current hour.
            numeric = all(_float(item) is not None for item in value) if value else False
            if numeric:
                start = base_at or now.replace(minute=0, second=0, microsecond=0)
                for idx, item in enumerate(value):
                    add(start + timedelta(hours=idx), _float(item))
                return
            for item in value:
                walk(item, base_at)

    walk(raw)
    unique: dict[datetime, PricePoint] = {}
    for point in found:
        unique[point.at] = point
    return sorted(unique.values(), key=lambda p: p.at)


def build_hphc_points(
    now: datetime,
    settings: dict[str, Any],
    hp_price: float | None,
    hc_price: float | None,
    *,
    horizon_hours: int = 24,
    step_minutes: int = 15,
) -> list[PricePoint]:
    if hp_price is None or hc_price is None:
        return []
    step = max(int(step_minutes), 5)
    start = now.replace(second=0, microsecond=0)
    # Align on the previous step boundary to make comparisons deterministic.
    start = start.replace(minute=(start.minute // step) * step)
    count = int(max(horizon_hours, 1) * 60 / step) + 1
    return [
        PricePoint(
            at=start + timedelta(minutes=idx * step),
            price=float(hp_price if tariff_period(start + timedelta(minutes=idx * step), settings) == "HP" else hc_price),
            source="HP_HC",
        )
        for idx in range(count)
    ]


def merge_price_points(*series: Iterable[PricePoint]) -> list[PricePoint]:
    merged: dict[datetime, PricePoint] = {}
    for points in series:
        for point in points:
            merged[point.at] = point
    return sorted(merged.values(), key=lambda p: p.at)


def _price_at(points: list[PricePoint], at: datetime) -> float | None:
    if not points:
        return None
    candidate: PricePoint | None = None
    for point in points:
        if point.at <= at:
            candidate = point
        else:
            break
    if candidate is not None:
        return candidate.price
    return points[0].price


def average_price(points: list[PricePoint], start: datetime, duration_hours: float, *, sample_minutes: int = 15) -> float | None:
    if not points:
        return None
    duration_minutes = max(int(round(max(duration_hours, 0.1) * 60)), sample_minutes)
    samples: list[float] = []
    for minute in range(0, duration_minutes, sample_minutes):
        price = _price_at(points, start + timedelta(minutes=minute))
        if price is None:
            return None
        samples.append(price)
    return sum(samples) / len(samples) if samples else None


def best_start_window(
    points: list[PricePoint],
    now: datetime,
    duration_hours: float,
    horizon_hours: int,
) -> tuple[datetime | None, float | None]:
    if not points:
        return None, None
    horizon_end = now + timedelta(hours=max(horizon_hours, 1))
    candidates = [p.at for p in points if now <= p.at <= horizon_end]
    if now not in candidates:
        candidates.insert(0, now)
    best_at: datetime | None = None
    best_price: float | None = None
    for start in candidates:
        avg = average_price(points, start, duration_hours)
        if avg is None:
            continue
        if best_price is None or avg < best_price:
            best_at, best_price = start, avg
    return best_at, best_price


def evaluate_market(
    *,
    now: datetime,
    snapshot: EnergySnapshot,
    prices: dict[str, Any],
    settings: dict[str, Any],
    import_points: list[PricePoint],
) -> EconomicDecision:
    regime = str(prices.get("regime") or TARIFF_TOU)
    current_buy = _float(prices.get("active_buy"))
    export_value = _float(prices.get("export_value"))
    horizon = int(float(settings.get("economic_horizon_hours", 24.0)))
    min_saving = float(settings.get("economic_min_saving_eur_kwh", 0.02))
    export_margin = float(settings.get("economic_export_margin_eur_kwh", 0.01))
    surplus_min = float(settings.get("economic_solar_surplus_min_w", 250.0))

    best_at, best_buy = best_start_window(import_points, now, 1.0, horizon)
    saving = (current_buy - best_buy) if current_buy is not None and best_buy is not None else None
    forecast_count = len(import_points)
    confidence = "HAUTE" if (regime == TARIFF_TOU and current_buy is not None) or forecast_count >= 6 else ("MOYENNE" if forecast_count >= 2 else "FAIBLE")

    if not bool(settings.get("economic_optimizer_enabled", True)):
        return EconomicDecision(
            "DESACTIVE", "Optimisation économique désactivée",
            "La couche économique est désactivée par l'utilisateur.", regime, "HAUTE", True,
            False, False, current_buy, export_value, best_buy, best_at, saving, horizon, forecast_count,
            application="DESACTIVE",
        )

    # Compensation remains a hard economic rule for the inverter: produce all
    # available PV. This module only reports the rule; it never publishes it on
    # Energy Bus and does not alter PRI here.
    if str(settings.get("network_policy")) == NETWORK_POLICY_COMPENSATION:
        return EconomicDecision(
            "COMPENSATION_MAX_PV", "Produire au maximum",
            "Politique Compensation : la production photovoltaïque disponible doit rester libérée à 100 %.",
            regime, confidence, True, False, True, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )

    if current_buy is None:
        return EconomicDecision(
            "PRIX_INDISPONIBLE", "Attendre les tarifs",
            "Prix d'achat indisponible : FoxCat refuse une décision économique non chiffrée.",
            regime, "FAIBLE", False, False, False, None, export_value, best_buy, best_at, None,
            horizon, forecast_count,
        )

    has_surplus = snapshot.export_w >= surplus_min
    if has_surplus and export_value is not None and export_value < 0:
        return EconomicDecision(
            "ABSORBER_SURPLUS", "Autoconsommer maintenant",
            f"La réinjection coûte {abs(export_value):.3f} €/kWh : absorber le surplus est prioritaire.",
            regime, confidence, True, True, False, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )

    if has_surplus and export_value is not None and best_buy is not None and export_value > best_buy + export_margin:
        return EconomicDecision(
            "EXPORTER_ET_REPORTER", "Exporter maintenant, consommer plus tard",
            f"Réinjection {export_value:.3f} €/kWh > meilleur achat futur {best_buy:.3f} €/kWh + marge : l'export est économiquement supérieur.",
            regime, confidence, False, False, True, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )

    if has_surplus and (export_value is None or export_value + export_margin < current_buy):
        return EconomicDecision(
            "AUTOCONSOMMER", "Autoconsommer le solaire",
            "Le coût d'opportunité de l'énergie solaire est inférieur au prix d'achat réseau actuel.",
            regime, confidence, True, True, False, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )

    if regime == TARIFF_DYNAMIC:
        if current_buy < 0:
            return EconomicDecision(
                "PRIX_ACHAT_NEGATIF", "Consommer maintenant",
                f"Prix d'achat négatif ({current_buy:.3f} €/kWh) : le réseau rémunère ou réduit le coût de la consommation.",
                regime, confidence, True, False, False, current_buy, export_value, best_buy, best_at, saving,
                horizon, forecast_count,
            )
        if saving is not None and saving > min_saving and best_at is not None and best_at > now + timedelta(minutes=10):
            return EconomicDecision(
                "ATTENDRE_MEILLEUR_PRIX", "Attendre un meilleur prix",
                f"Économie potentielle {saving:.3f} €/kWh en différant jusqu'au meilleur créneau connu.",
                regime, confidence, False, False, False, current_buy, export_value, best_buy, best_at, saving,
                horizon, forecast_count,
            )
        return EconomicDecision(
            "CONSOMMER_MAINTENANT", "Consommer maintenant",
            "Le prix actuel est proche du meilleur prix connu sur l'horizon analysé.",
            regime, confidence, True, False, False, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )

    # Fixed HP/HC: future prices are deterministic once HP and HC are known.
    period = str(prices.get("period") or tariff_period(now, settings))
    if period == "HC":
        return EconomicDecision(
            "CONSOMMER_HC", "Profiter des heures creuses",
            "Période HC active : les charges flexibles peuvent fonctionner au tarif bas.",
            regime, "HAUTE", True, False, False, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )
    if saving is not None and saving > min_saving:
        return EconomicDecision(
            "ATTENDRE_HC", "Attendre les heures creuses",
            f"Le prochain meilleur créneau réduit le coût estimé de {saving:.3f} €/kWh.",
            regime, "HAUTE", False, False, False, current_buy, export_value, best_buy, best_at, saving,
            horizon, forecast_count,
        )
    return EconomicDecision(
        "HP_ACCEPTABLE", "Consommer si nécessaire",
        "L'écart HP/HC ne dépasse pas la marge économique configurée.",
        regime, "HAUTE", True, False, False, current_buy, export_value, best_buy, best_at, saving,
        horizon, forecast_count,
    )


def recommend_flexible_load(
    *,
    now: datetime,
    snapshot: EnergySnapshot,
    prices: dict[str, Any],
    settings: dict[str, Any],
    import_points: list[PricePoint],
    duration_hours: float | None,
    energy_kwh: float | None,
    active: bool,
) -> dict[str, Any]:
    """Compare a machine start now with future starts without commanding it."""
    if active:
        return {
            "decision": "CYCLE_EN_COURS",
            "label": "Cycle en cours — ne pas interrompre",
            "allow_start": True,
            "reason": "Un cycle actif/protégé reste souverain sur l'optimisation économique.",
            "confidence": "HAUTE",
        }

    duration = max(float(duration_hours or 1.0), 0.25)
    energy = max(float(energy_kwh or 1.0), 0.05)
    avg_power_w = energy / duration * 1000.0
    current_buy = _float(prices.get("active_buy"))
    export_value = _float(prices.get("export_value"))
    horizon = int(float(settings.get("economic_horizon_hours", 24.0)))
    min_saving = float(settings.get("economic_min_saving_eur_kwh", 0.02))
    export_margin = float(settings.get("economic_export_margin_eur_kwh", 0.01))

    if current_buy is None:
        return {
            "decision": "PRIX_INDISPONIBLE", "label": "Prix indisponible", "allow_start": False,
            "reason": "Pas de prix d'achat fiable pour comparer le cycle.", "confidence": "FAIBLE",
            "duration_h": round(duration, 3), "energy_kwh": round(energy, 3),
        }

    best_at, best_cost = best_start_window(import_points, now, duration, horizon)
    grid_now_cost = average_price(import_points, now, duration) or current_buy

    # If current exported solar can feed part of the average machine load, its
    # economic cost is the export revenue that would be abandoned, not 0 €/kWh.
    solar_fraction = min(max(snapshot.export_w, 0.0), avg_power_w) / avg_power_w if avg_power_w > 0 else 0.0
    solar_fraction = max(0.0, min(solar_fraction, 1.0))
    pv_opportunity = export_value if export_value is not None else 0.0
    effective_now = solar_fraction * pv_opportunity + (1.0 - solar_fraction) * grid_now_cost

    saving = (effective_now - best_cost) if best_cost is not None else 0.0
    confidence = "HAUTE" if len(import_points) >= 6 or str(prices.get("regime")) == TARIFF_TOU else ("MOYENNE" if len(import_points) >= 2 else "FAIBLE")

    if solar_fraction >= 0.5 and export_value is not None and export_value < 0:
        allow = True
        decision = "ABSORBER_SURPLUS"
        reason = "Le cycle absorbe un surplus dont la réinjection est actuellement payante/défavorable."
    elif solar_fraction >= 0.5 and export_value is not None and best_cost is not None and export_value > best_cost + export_margin:
        allow = False
        decision = "EXPORTER_ET_REPORTER"
        reason = "Vendre le surplus maintenant puis exécuter le cycle au meilleur prix futur est plus favorable."
    elif best_cost is not None and saving > min_saving and best_at is not None and best_at > now + timedelta(minutes=10):
        allow = False
        decision = "REPORTER"
        reason = f"Reporter le cycle économise environ {saving:.3f} €/kWh sur son profil moyen."
    else:
        allow = True
        decision = "DEMARRER"
        reason = "Le coût du démarrage immédiat est compétitif sur l'horizon analysé."

    return {
        "decision": decision,
        "label": {
            "ABSORBER_SURPLUS": "Démarrer pour absorber le surplus",
            "EXPORTER_ET_REPORTER": "Exporter maintenant et reporter",
            "REPORTER": "Reporter le démarrage",
            "DEMARRER": "Démarrer maintenant",
        }.get(decision, decision),
        "allow_start": allow,
        "reason": reason,
        "confidence": confidence,
        "duration_h": round(duration, 3),
        "energy_kwh": round(energy, 3),
        "average_power_w": round(avg_power_w, 1),
        "solar_fraction_now": round(solar_fraction, 3),
        "effective_cost_now_eur_kwh": round(effective_now, 5),
        "best_future_cost_eur_kwh": round(best_cost, 5) if best_cost is not None else None,
        "best_future_at": best_at.isoformat() if best_at else None,
        "saving_eur_kwh": round(max(saving, 0.0), 5),
    }
