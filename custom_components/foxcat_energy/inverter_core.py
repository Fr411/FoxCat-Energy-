from __future__ import annotations

from dataclasses import dataclass
from typing import Any

NETWORK_COMPENSATION = "Compensation"
NETWORK_BILLED_EXPORT = "Injection facturée"


@dataclass(slots=True)
class InverterDecision:
    current_level: int
    target_level: int
    action: str
    reason: str
    pv_limit_w: float
    pv_ratio: float
    pv_at_limit: bool
    more_solar_possible: bool
    max_solar_reached: bool


class InverterCore:
    """Second cœur FoxCat : uniquement responsable de la puissance onduleur."""

    def decide(
        self,
        snapshot: Any,
        current_level: int,
        settings: dict[str, Any],
        network_policy: str,
        bus_state: dict[str, Any] | None = None,
    ) -> InverterDecision:
        inverter_w = max(float(settings.get("inverter_power_w", 4000.0)), 1.0)
        step_pct = max(int(round(float(settings.get("pri_step_percent", 10.0)))), 10)
        tolerance_w = max(float(settings.get("pri_pv_compare_tolerance_w", 200.0)), 0.0)
        ratio_threshold = min(max(float(settings.get("pri_ceiling_ratio", 0.92)), 0.50), 1.0)

        current = max(0, min(100, int(current_level)))
        limit_w = inverter_w * current / 100.0
        pv_w = max(float(snapshot.pv_w), 0.0)
        ratio = (pv_w / limit_w) if limit_w > 0 else 0.0
        pv_at_limit = (
            current > 0
            and (pv_w >= max(limit_w - tolerance_w, 0.0) or ratio >= ratio_threshold)
        )
        max_solar = current > 0 and not pv_at_limit
        more_possible = current < 100 and pv_at_limit

        # Compensation : le réseau est tampon. On ne bride pas volontairement
        # la production PV; l'EMS principal reste libre de gérer ses charges.
        if network_policy == NETWORK_COMPENSATION:
            target = min(current + step_pct, 100) if current < 100 else 100
            return InverterDecision(
                current, target,
                "LIBERATION" if target > current else "MAINTIEN",
                "Compensation : onduleur libéré progressivement vers 100 %, réseau utilisé comme tampon.",
                limit_w, ratio, pv_at_limit, more_possible, max_solar,
            )

        # Injection facturée : léger import recherché pour éviter le rejet.
        export_limit = max(float(settings.get("network_billed_export_max_w", 50.0)), 0.0)
        import_target = max(float(settings.get("network_billed_import_target_w", 100.0)), 0.0)
        import_high = max(float(settings.get("network_billed_import_max_w", 250.0)), import_target)

        export_w = max(float(snapshot.export_w), 0.0)
        import_w = max(float(snapshot.import_w), 0.0)

        if export_w > export_limit:
            target = max(current - step_pct, 0)
            return InverterDecision(
                current, target, "REDUCTION",
                f"Injection facturée : export {export_w:.0f} W > {export_limit:.0f} W, réduction d'un palier.",
                limit_w, ratio, pv_at_limit, more_possible, max_solar,
            )

        if import_w > import_high:
            if current < 100 and pv_at_limit:
                target = min(current + step_pct, 100)
                return InverterDecision(
                    current, target, "LIBERATION",
                    f"Import {import_w:.0f} W et PV au plafond ({pv_w:.0f}/{limit_w:.0f} W) : libération d'un palier.",
                    limit_w, ratio, pv_at_limit, True, False,
                )
            return InverterDecision(
                current, current, "MAINTIEN",
                f"Import {import_w:.0f} W mais PV sous plafond ({pv_w:.0f}/{limit_w:.0f} W) : maximum solaire instantané atteint.",
                limit_w, ratio, pv_at_limit, False, True,
            )

        return InverterDecision(
            current, current, "MAINTIEN",
            f"Zone réseau maîtrisée : export={export_w:.0f} W, import={import_w:.0f} W, cible léger import ≈ {import_target:.0f} W.",
            limit_w, ratio, pv_at_limit, more_possible, max_solar,
        )
