from __future__ import annotations

import math

from .models import EnergySnapshot, PriDecision


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score(import_w: float, export_w: float, weight_import: float, weight_export: float) -> float:
    return max(import_w, 0.0) * weight_import + max(export_w, 0.0) * weight_export


def house_target_level(house_w: float, step_w: float, weight_import: float, weight_export: float) -> tuple[int, float, float]:
    if step_w <= 0:
        return 100, 0.0, 0.0
    low_steps = int(clamp(math.floor(max(house_w, 0.0) / step_w), 0, 10))
    high_steps = int(clamp(math.ceil(max(house_w, 0.0) / step_w), 0, 10))
    low_power = low_steps * step_w
    high_power = high_steps * step_w
    low_score = score(max(house_w - low_power, 0.0), max(low_power - house_w, 0.0), weight_import, weight_export)
    high_score = score(max(house_w - high_power, 0.0), max(high_power - house_w, 0.0), weight_import, weight_export)
    target = low_steps * 10 if low_score <= high_score else high_steps * 10
    return target, low_score, high_score


def decide_zero(snapshot: EnergySnapshot, current_level: int, settings: dict[str, object]) -> PriDecision:
    """Zéro injection piloté par le réseau avec best-effort anti-oscillation.

    La réinjection réelle est l'erreur souveraine. La consommation maison reste
    un diagnostic uniquement. Une marche de 10 % n'est appliquée que si son
    effet projeté ne transforme pas un petit export résiduel en import excessif.
    Cela permet un zéro total lorsque les paliers le permettent, ou un zéro
    partiel stable lorsque 400 W de granularité rendent le zéro exact impossible.
    """
    step_w = float(settings["pri_step_w"])
    export_trigger = float(settings["pri_export_acceptable_w"])
    import_trigger = float(settings["pri_import_acceptable_w"])
    export_opt = float(settings["pri_export_optimal_w"])
    import_opt = float(settings["pri_import_optimal_w"])
    wi = float(settings["pri_weight_import"])
    we = float(settings["pri_weight_export"])

    house_target, _, _ = house_target_level(snapshot.house_w, step_w, wi, we)
    current_score = score(snapshot.import_w, snapshot.export_w, wi, we)

    if snapshot.export_w > export_trigger and current_level > 0:
        projected_export = max(snapshot.export_w - step_w, 0.0)
        projected_import = max(step_w - snapshot.export_w, 0.0)
        target_score = score(projected_import, projected_export, wi, we)

        if projected_import > import_trigger:
            return PriDecision(
                "maintien", current_level, current_level,
                f"Zéro partiel : {snapshot.export_w:.0f} W réinjectés mais la marche inférieure projetterait {projected_import:.0f} W de prélèvement.",
                current_score, current_score, house_target,
            )

        target = max(current_level - 10, 0)
        return PriDecision(
            "descente", current_level, target,
            f"Réinjection {snapshot.export_w:.0f} W > {export_trigger:.0f} W : descente d'une marche vers le zéro injection.",
            current_score, target_score, house_target,
        )

    if snapshot.export_w > export_trigger and current_level <= 0:
        return PriDecision(
            "maintien", current_level, current_level,
            "Zéro partiel : PRI déjà au minimum, réinjection résiduelle non supprimable par RRCR.",
            current_score, current_score, house_target,
        )

    if snapshot.import_w > import_trigger and current_level < 100:
        projected_import = max(snapshot.import_w - step_w, 0.0)
        projected_export = max(step_w - snapshot.import_w, 0.0)
        target_score = score(projected_import, projected_export, wi, we)

        if projected_export > export_trigger:
            return PriDecision(
                "maintien", current_level, current_level,
                f"Maintien anti-oscillation : une remontée projetterait {projected_export:.0f} W de réinjection.",
                current_score, current_score, house_target,
            )

        target = min(current_level + 10, 100)
        return PriDecision(
            "remontee", current_level, target,
            f"Prélèvement {snapshot.import_w:.0f} W > {import_trigger:.0f} W : remontée prudente d'une marche.",
            current_score, target_score, house_target,
        )

    if snapshot.export_w <= export_opt and snapshot.import_w <= import_opt:
        reason = "Zéro injection atteint : réseau dans la zone optimale."
    else:
        reason = "Zéro injection stable dans l'hystérésis PRI."
    return PriDecision("maintien", current_level, current_level, reason, current_score, current_score, house_target)

def decide_dynamic(snapshot: EnergySnapshot, current_level: int, settings: dict[str, object], injection_price: float | None, boiler_absorbing: bool) -> PriDecision:
    pv_min = float(settings["pri_pv_minimum_w"])
    injection_lucrative_threshold = float(settings["dynamic_injection_lucrative_threshold"])
    export_threshold = float(settings["pri_export_threshold_dynamic_w"])
    import_threshold = float(settings["pri_import_threshold_dynamic_w"])
    step_w = float(settings["pri_step_w"])

    if snapshot.pv_w < pv_min:
        target = min(current_level + 10, 100) if current_level < 100 else 100
        direction = "remontee" if target > current_level else "maintien"
        return PriDecision(direction, current_level, target, "Production PV trop faible : libération progressive de l'onduleur.")

    if injection_price is None:
        target = min(current_level + 10, 100) if current_level < 100 else 100
        direction = "remontee" if target > current_level else "maintien"
        return PriDecision(direction, current_level, target, "Prix d'injection indisponible : fail-safe à 100 %.")

    if injection_price < injection_lucrative_threshold:
        target = min(current_level + 10, 100) if current_level < 100 else 100
        direction = "remontee" if target > current_level else "maintien"
        return PriDecision(direction, current_level, target, "Injection rémunératrice : onduleur libéré progressivement.")

    if snapshot.import_w > import_threshold and current_level < 100:
        target = min(current_level + 10, 100)
        return PriDecision("remontee", current_level, target, "Import réseau : remontée PRI pour privilégier l'autoconsommation.")

    if snapshot.export_w > export_threshold and current_level > 0:
        projected_export = snapshot.export_w - step_w
        if projected_export >= 0:
            target = max(current_level - 10, 0)
            return PriDecision("descente", current_level, target, "Export non rémunérateur : réduction d'une marche sans import projeté.")
        return PriDecision("maintien", current_level, current_level, "La marche inférieure provoquerait volontairement un import réseau.")

    return PriDecision("maintien", current_level, current_level, "PRI dynamique stable.")
