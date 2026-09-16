from __future__ import annotations
import math
from .models import EnergySnapshot, PriDecision

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def quantize_10(value: float) -> int:
    return int(clamp(round(value / 10.0) * 10, 0, 100))

def pi_zero(
    snapshot: EnergySnapshot,
    current_level: int,
    integral: float,
    settings: dict[str, object],
) -> tuple[PriDecision, float, float]:
    """PRI PI discret 30 s. Positif réseau = export, négatif = import.

    La sortie continue est conservée en diagnostic puis quantifiée physiquement
    sur les pas RRCR de 10 %. L'intégrale est bornée (anti-windup).
    """
    dt = float(settings.get("pri_pi_dt_s", 30.0))
    target_export = float(settings.get("pri_pi_target_export_w", 75.0))
    kp = float(settings.get("pri_pi_kp", 0.012))
    ki = float(settings.get("pri_pi_ki", 0.00010))
    i_limit = float(settings.get("pri_pi_integral_limit_ws", 120000.0))
    deadband = float(settings.get("pri_pi_deadband_w", 100.0))

    # >0 = trop d'export => il faut réduire le niveau PRI.
    error = snapshot.grid_net_w - target_export
    if abs(error) <= deadband:
        error = 0.0

    proposed_i = clamp(integral + error * dt, -i_limit, i_limit)
    correction_pct = kp * error + ki * proposed_i
    continuous = clamp(float(current_level) - correction_pct, 0.0, 100.0)
    target = quantize_10(continuous)

    # Anti-windup conditionnel aux saturations.
    if (continuous <= 0.0 and error > 0) or (continuous >= 100.0 and error < 0):
        proposed_i = integral
        correction_pct = kp * error + ki * proposed_i
        continuous = clamp(float(current_level) - correction_pct, 0.0, 100.0)
        target = quantize_10(continuous)

    # Une seule marche physique par trame pour préserver la stabilité.
    if target < current_level:
        target = max(current_level - 10, 0)
        direction = "descente"
    elif target > current_level:
        target = min(current_level + 10, 100)
        direction = "remontee"
    else:
        direction = "maintien"

    reason = (
        f"PRI-PI : réseau={snapshot.grid_net_w:.0f} W, consigne export={target_export:.0f} W, "
        f"erreur={error:.0f} W, sortie continue={continuous:.1f} %, cible RRCR={target} %."
    )
    return PriDecision(direction,current_level,target,reason,0.0,0.0,None), proposed_i, continuous

def decide_zero(snapshot: EnergySnapshot, current_level: int, settings: dict[str, object]) -> PriDecision:
    # Compatibilité tests/outils : décision PI sans mémoire externe.
    return pi_zero(snapshot,current_level,0.0,settings)[0]

def decide_dynamic(snapshot: EnergySnapshot, current_level: int, settings: dict[str, object],
                   injection_price: float | None, boiler_absorbing: bool) -> PriDecision:
    # Le dynamique conserve la libération si l'injection est rémunératrice,
    # sinon utilise le même PI réseau.
    lucrative=float(settings.get("dynamic_injection_lucrative_threshold",-0.01))
    if injection_price is None or injection_price < lucrative:
        target=min(current_level+10,100)
        return PriDecision("remontee" if target>current_level else "maintien",current_level,target,
                           "Prix d'injection favorable/inconnu : libération progressive PRI.")
    return decide_zero(snapshot,current_level,settings)
