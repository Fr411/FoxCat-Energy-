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
    score_current: float = 0.0
    score_target: float = 0.0
    house_target_level: int = 100
    estimated_house_w: float = 0.0
    target_pv_w: float = 0.0
    predicted_import_w: float = 0.0
    predicted_export_w: float = 0.0


class InverterCore:
    """Cœur PRI souverain FoxCat.

    V1.5.6 applique une règle volontairement simple et stricte : chaque trame
    énergétique valide recalcule le meilleur palier RRCR et peut le commander
    immédiatement. Aucune hystérésis, temporisation, ACK antérieur, état boiler,
    mode EMS ou hypothèse de potentiel solaire ne bloque ce recalcul.

    Le calcul est feed-forward sur la consommation maison normalisée par FoxCat,
    puis corrigé à la trame suivante par les nouvelles mesures réseau. Une erreur
    ponctuelle est donc acceptée : la trame suivante la corrige.
    """

    @staticmethod
    def _score_grid(
        import_w: float,
        export_w: float,
        *,
        import_target_w: float,
        import_max_w: float,
        export_max_w: float,
        weight_import: float,
        weight_export: float,
    ) -> float:
        """Score d'un palier simulé ; plus petit = meilleur."""
        import_w = max(float(import_w), 0.0)
        export_w = max(float(export_w), 0.0)
        score = abs(import_w - import_target_w) * weight_import
        score += export_w * weight_export
        if import_w > import_max_w:
            score += (import_w - import_max_w) * weight_import * 4.0
        if export_w > export_max_w:
            score += (export_w - export_max_w) * weight_export * 4.0
        return score

    @staticmethod
    def _nearest_level_for_power(power_w: float, inverter_w: float) -> int:
        if inverter_w <= 0:
            return 100
        raw = max(0.0, min(100.0, float(power_w) / inverter_w * 100.0))
        return max(0, min(100, int(round(raw / 10.0) * 10)))

    def decide(
        self,
        snapshot: Any,
        current_level: int,
        settings: dict[str, Any],
        network_policy: str,
        bus_state: dict[str, Any] | None = None,
    ) -> InverterDecision:
        inverter_w = max(float(settings.get("inverter_power_w", 4000.0)), 1.0)
        tolerance_w = max(float(settings.get("pri_pv_compare_tolerance_w", 200.0)), 0.0)
        ratio_threshold = min(max(float(settings.get("pri_ceiling_ratio", 0.92)), 0.50), 1.0)

        current = max(0, min(100, int(current_level)))
        current_limit_w = inverter_w * current / 100.0
        pv_w = max(float(snapshot.pv_w), 0.0)
        house_w = max(float(snapshot.house_w), 0.0)
        export_w = max(float(snapshot.export_w), 0.0)
        import_w = max(float(snapshot.import_w), 0.0)

        ratio = (pv_w / current_limit_w) if current_limit_w > 0 else 0.0
        pv_at_limit = (
            current > 0
            and (pv_w >= max(current_limit_w - tolerance_w, 0.0) or ratio >= ratio_threshold)
        )

        # En compensation, l'objectif est sans ambiguïté : aucune limitation PRI.
        # La décision est tout de même recalculée à chaque trame et la commande
        # peut passer directement au palier idéal, ici 100 %.
        if network_policy == NETWORK_COMPENSATION:
            target = 100
            target_limit_w = inverter_w
            predicted_grid_w = target_limit_w - house_w
            predicted_export = max(predicted_grid_w, 0.0)
            predicted_import = max(-predicted_grid_w, 0.0)
            action = "LIBERATION" if target > current else "MAINTIEN"
            return InverterDecision(
                current_level=current,
                target_level=target,
                action=action,
                reason=(
                    "PRI souverain : politique Compensation, recalcul direct vers 100 %. "
                    f"Maison={house_w:.0f} W, PV={pv_w:.0f} W."
                ),
                pv_limit_w=current_limit_w,
                pv_ratio=ratio,
                pv_at_limit=pv_at_limit,
                more_solar_possible=target < 100,
                max_solar_reached=target == 100,
                house_target_level=100,
                estimated_house_w=house_w,
                target_pv_w=target_limit_w,
                predicted_import_w=predicted_import,
                predicted_export_w=predicted_export,
            )

        export_limit = max(float(settings.get("network_billed_export_max_w", 50.0)), 0.0)
        import_target = max(float(settings.get("network_billed_import_target_w", 100.0)), 0.0)
        import_high = max(float(settings.get("network_billed_import_max_w", 250.0)), import_target)
        weight_import = max(float(settings.get("pri_weight_import", 1.0)), 0.01)
        weight_export = max(float(settings.get("pri_weight_export", 2.0)), 0.01)

        # La consommation maison FoxCat est la grandeur feed-forward souveraine.
        # Cela permet une remontée immédiate du PRI dès que la maison monte,
        # avant même que le compteur réseau ait totalement reflété la variation.
        estimated_house_w = house_w
        target_pv_w = max(estimated_house_w - import_target, 0.0)
        house_target_level = self._nearest_level_for_power(target_pv_w, inverter_w)

        current_score = self._score_grid(
            import_w,
            export_w,
            import_target_w=import_target,
            import_max_w=import_high,
            export_max_w=export_limit,
            weight_import=weight_import,
            weight_export=weight_export,
        )

        # Chaque niveau est simulé comme plafond immédiatement disponible.
        # Il n'existe volontairement plus de garde "PV au plafond" : si le soleil
        # réel ne permet pas le niveau demandé, la prochaine trame le constatera
        # et recalculera. L'algorithme ne reste donc jamais bloqué par une ancienne
        # hypothèse de potentiel solaire.
        candidates: list[tuple[float, int, float, float, float]] = []
        for level in range(0, 101, 10):
            candidate_pv_w = inverter_w * level / 100.0
            grid_w = candidate_pv_w - estimated_house_w
            predicted_export_w = max(grid_w, 0.0)
            predicted_import_w = max(-grid_w, 0.0)
            score = self._score_grid(
                predicted_import_w,
                predicted_export_w,
                import_target_w=import_target,
                import_max_w=import_high,
                export_max_w=export_limit,
                weight_import=weight_import,
                weight_export=weight_export,
            )
            candidates.append((score, level, predicted_import_w, predicted_export_w, candidate_pv_w))

        # Aucun seuil de gain et aucune hystérésis : le meilleur palier gagne à
        # chaque trame. En cas de score strictement identique, on choisit le plus
        # proche de la cible théorique maison puis le niveau le plus faible afin
        # de privilégier l'absence de réinjection.
        best = min(
            candidates,
            key=lambda row: (row[0], abs(row[1] - house_target_level), row[1]),
        )
        best_score, target, predicted_import, predicted_export, predicted_pv = best

        action = "REDUCTION" if target < current else "LIBERATION" if target > current else "MAINTIEN"
        target_limit_w = inverter_w * target / 100.0
        reason = (
            "PRI souverain : recalcul intégral sans blocage "
            f"{current}% -> {target}%. Maison={estimated_house_w:.0f} W, "
            f"PV cible≈{target_pv_w:.0f} W, plafond={target_limit_w:.0f} W, "
            f"réseau mesuré={export_w:.0f} W export/{import_w:.0f} W import, "
            f"réseau simulé={predicted_export:.0f} W export/{predicted_import:.0f} W import."
        )

        target_ratio = (predicted_pv / target_limit_w) if target_limit_w > 0 else 0.0
        target_at_limit = (
            target > 0
            and (
                predicted_pv >= max(target_limit_w - tolerance_w, 0.0)
                or target_ratio >= ratio_threshold
            )
        )

        return InverterDecision(
            current_level=current,
            target_level=target,
            action=action,
            reason=reason,
            pv_limit_w=current_limit_w,
            pv_ratio=ratio,
            pv_at_limit=pv_at_limit,
            more_solar_possible=(target < 100 and target_at_limit),
            max_solar_reached=(target == 100 or (target > 0 and not target_at_limit)),
            score_current=current_score,
            score_target=best_score,
            house_target_level=house_target_level,
            estimated_house_w=estimated_house_w,
            target_pv_w=target_pv_w,
            predicted_import_w=predicted_import,
            predicted_export_w=predicted_export,
        )
