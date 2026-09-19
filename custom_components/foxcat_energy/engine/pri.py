from __future__ import annotations

import math

from .models import EnergySnapshot, PriDecision


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score(import_w: float, export_w: float, weight_import: float, weight_export: float) -> float:
    """Conservé pour compatibilité diagnostics/API existants."""
    return max(import_w, 0.0) * weight_import + max(export_w, 0.0) * weight_export


def house_target_level(
    house_w: float,
    step_w: float,
    weight_import: float = 1.0,
    weight_export: float = 1.0,
) -> tuple[int, float, float]:
    """
    Cible feed-forward FoxCat.

    Contrairement à l'ancienne carte qui utilisait floor(), FoxCat 1.4.3
    utilise ceil() afin de ne pas créer volontairement un prélèvement réseau.

      1..400 W     -> 10 %
      401..800 W   -> 20 %
      ...
      3601..4000 W -> 100 %

    Les scores low/high sont conservés dans la signature pour compatibilité.
    """
    if step_w <= 0:
        return 100, 0.0, 0.0

    house = max(float(house_w), 0.0)
    low_steps = int(clamp(math.floor(house / step_w), 0, 10))
    high_steps = int(clamp(math.ceil(house / step_w), 0, 10))

    # 0 W réel peut rester à 0 %. Toute charge > 0 W prend le palier supérieur.
    target_steps = 0 if house <= 0 else high_steps
    target = int(clamp(target_steps * 10, 0, 100))

    low_power = low_steps * step_w
    high_power = high_steps * step_w
    low_score = score(
        max(house - low_power, 0.0),
        max(low_power - house, 0.0),
        weight_import,
        weight_export,
    )
    high_score = score(
        max(house - high_power, 0.0),
        max(high_power - house, 0.0),
        weight_import,
        weight_export,
    )
    return target, low_score, high_score


def _solar_state(snapshot: EnergySnapshot, current_level: int, settings: dict[str, object]) -> tuple[str, float]:
    """
    Compare le PV réel au plafond PRI actuel.

    PV_LIMITED       : le PV touche approximativement le plafond PRI.
    SUN_LIMITED      : le PV est nettement sous le plafond -> soleil limitant.
    PRI_INCONSISTENT : PV mesuré au-dessus du plafond attendu.
    """
    step_w = float(settings.get("pri_step_w", 400.0))
    tolerance = float(settings.get("pri_pv_compare_tolerance_w", 200.0))
    limit_w = step_w * (max(current_level, 0) / 10.0)

    if current_level <= 0:
        return "UNKNOWN", limit_w

    error = snapshot.pv_w - limit_w
    if abs(error) <= tolerance:
        return "PV_LIMITED", limit_w
    if snapshot.pv_w < limit_w - tolerance:
        return "SUN_LIMITED", limit_w
    return "PRI_INCONSISTENT", limit_w


def decide_zero(snapshot: EnergySnapshot, current_level: int, settings: dict[str, object]) -> PriDecision:
    """
    PRI hybride FoxCat 1.4.3.

    Priorités physiques :
      1. Import réel -> libérer l'onduleur (+10 %).
      2. Export réel excessif -> réduire (-10 %) si la marche projetée
         ne crée pas volontairement un import important.
      3. Zone réseau morte -> maintien.
      4. La cible maison sert de référence/diagnostic, jamais de raison
         pour descendre pendant qu'on prélève déjà du réseau.

    Une seule marche est proposée. Le coordinator conserve l'ACK RRCR
    et la validation sur vraie trame N+1.
    """
    step_w = float(settings["pri_step_w"])
    wi = float(settings.get("pri_weight_import", 1.0))
    we = float(settings.get("pri_weight_export", 1.0))
    export_deadband = float(settings.get("pri_export_acceptable_w", 150.0))
    import_deadband = float(settings.get("pri_import_acceptable_w", 200.0))

    house_target, _, _ = house_target_level(snapshot.house_w, step_w, wi, we)
    solar_state, pv_limit_w = _solar_state(snapshot, current_level, settings)

    # IMPORT : priorité absolue à l'autoconsommation.
    # Cas réel observé : PV 1.22 kW / import 1.04 kW / PRI 90 %.
    # Il est interdit de descendre vers la cible maison dans cette situation.
    if snapshot.import_w > import_deadband:
        if current_level < 100:
            target = min(current_level + 10, 100)
            return PriDecision(
                "remontee",
                current_level,
                target,
                (
                    f"Import {snapshot.import_w:.0f} W > {import_deadband:.0f} W : "
                    f"libération PRI. PV={snapshot.pv_w:.0f} W, plafond={pv_limit_w:.0f} W, "
                    f"état solaire={solar_state}, cible maison={house_target}%."
                ),
                snapshot.import_w,
                max(snapshot.import_w - step_w, 0.0),
                house_target,
            )
        return PriDecision(
            "maintien",
            current_level,
            current_level,
            (
                f"Import {snapshot.import_w:.0f} W mais PRI déjà à 100 % : "
                f"le réseau ne peut pas être corrigé par davantage de libération PV "
                f"(état solaire={solar_state})."
            ),
            snapshot.import_w,
            snapshot.import_w,
            house_target,
        )

    # EXPORT : une marche de moins enlève environ 400 W de plafond.
    if snapshot.export_w > export_deadband and current_level > 0:
        projected_net = snapshot.export_w - step_w
        projected_export = max(projected_net, 0.0)
        projected_import = max(-projected_net, 0.0)

        # On accepte seulement le petit import contenu dans la zone morte.
        if projected_import <= import_deadband:
            target = max(current_level - 10, 0)
            return PriDecision(
                "descente",
                current_level,
                target,
                (
                    f"Export {snapshot.export_w:.0f} W > {export_deadband:.0f} W : "
                    f"descente d'une marche. Projection après -{step_w:.0f} W : "
                    f"export {projected_export:.0f} W / import {projected_import:.0f} W. "
                    f"Cible maison={house_target}%, état solaire={solar_state}."
                ),
                snapshot.export_w,
                projected_export + projected_import,
                house_target,
            )

        return PriDecision(
            "maintien",
            current_level,
            current_level,
            (
                f"Export {snapshot.export_w:.0f} W, mais -10 % projetterait "
                f"{projected_import:.0f} W d'import (> {import_deadband:.0f} W) : maintien."
            ),
            snapshot.export_w,
            snapshot.export_w,
            house_target,
        )

    # Zone morte : ne pas chasser quelques dizaines de watts.
    return PriDecision(
        "maintien",
        current_level,
        current_level,
        (
            f"Réseau dans la zone morte : import={snapshot.import_w:.0f} W, "
            f"export={snapshot.export_w:.0f} W. Cible maison={house_target}%, "
            f"état solaire={solar_state}."
        ),
        0.0,
        0.0,
        house_target,
    )


def decide_dynamic(
    snapshot: EnergySnapshot,
    current_level: int,
    settings: dict[str, object],
    injection_price: float | None,
    boiler_absorbing: bool,
) -> PriDecision:
    """
    Le tarif ne remplace pas la boucle physique.

    - prix d'injection inconnu : fail-safe, libération progressive ;
    - injection économiquement favorable selon la convention FoxCat existante :
      libération progressive ;
    - sinon : même régulation physique robuste que Zéro injection.
    """
    lucrative_threshold = float(settings["dynamic_injection_lucrative_threshold"])

    if injection_price is None:
        target = min(current_level + 10, 100)
        direction = "remontee" if target > current_level else "maintien"
        return PriDecision(
            direction, current_level, target,
            "Prix d'injection indisponible : fail-safe, libération progressive du PRI."
        )

    if injection_price < lucrative_threshold:
        target = min(current_level + 10, 100)
        direction = "remontee" if target > current_level else "maintien"
        return PriDecision(
            direction, current_level, target,
            "Injection économiquement favorable : libération progressive de l'onduleur."
        )

    # Si le boiler absorbe déjà le surplus, on laisse la boucle physique constater
    # le réseau réel : pas de décision tarifaire parallèle.
    return decide_zero(snapshot, current_level, settings)
