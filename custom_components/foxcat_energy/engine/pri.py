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
    step_w = float(settings["pri_step_w"])
    wi = float(settings["pri_weight_import"])
    we = float(settings["pri_weight_export"])
    export_opt = float(settings["pri_export_optimal_w"])
    import_opt = float(settings["pri_import_optimal_w"])
    margin = float(settings["pri_score_margin"])

    house_target, _, _ = house_target_level(snapshot.house_w, step_w, wi, we)
    current_score = score(snapshot.import_w, snapshot.export_w, wi, we)
    net_import_minus_export = snapshot.import_w - snapshot.export_w

    # One lower inverter stage means roughly step_w less PV, therefore +step_w on import-minus-export.
    net_down = net_import_minus_export + step_w
    down_import = max(net_down, 0.0)
    down_export = max(-net_down, 0.0)
    down_score = score(down_import, down_export, wi, we)

    # One higher inverter stage means roughly step_w more PV.
    net_up = net_import_minus_export - step_w
    up_import = max(net_up, 0.0)
    up_export = max(-net_up, 0.0)
    up_score = score(up_import, up_export, wi, we)

    if snapshot.export_w <= export_opt and snapshot.import_w <= import_opt:
        return PriDecision("maintien", current_level, current_level, "Réseau dans la zone optimale.", current_score, current_score, house_target)

    if snapshot.export_w > export_opt and current_level > 0 and down_score + margin < current_score:
        target = max(current_level - 10, 0)
        return PriDecision("descente", current_level, target, "Une marche inférieure améliore le compromis import/réinjection.", current_score, down_score, house_target)

    if snapshot.import_w > import_opt and current_level < 100 and up_score + margin < current_score:
        target = min(current_level + 10, 100)
        return PriDecision("remontee", current_level, target, "Une marche supérieure réduit le prélèvement sans dégrader le score.", current_score, up_score, house_target)

    return PriDecision("maintien", current_level, current_level, "Aucun palier adjacent n'améliore suffisamment le score.", current_score, current_score, house_target)


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

    if snapshot.export_w > export_threshold and current_level > 0 and not boiler_absorbing:
        projected_export = snapshot.export_w - step_w
        if projected_export >= 0:
            target = max(current_level - 10, 0)
            return PriDecision("descente", current_level, target, "Export non rémunérateur : réduction d'une marche sans import projeté.")
        return PriDecision("maintien", current_level, current_level, "La marche inférieure provoquerait volontairement un import réseau.")

    return PriDecision("maintien", current_level, current_level, "PRI dynamique stable.")
