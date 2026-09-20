from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class EnergyIntent:
    source: str
    action: str
    delta_w: float
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class EnergyBus:
    """Communication immédiate EMS CORE <-> EMS Onduleur.

    Le bus ne décide rien. Il mémorise les intentions et les états.
    Les commandes physiques onduleur sont consommées uniquement sur une
    nouvelle trame réseau.
    """

    def __init__(self) -> None:
        self.last_ems_intent: EnergyIntent | None = None
        self.inverter_state: dict[str, Any] = {
            "status": "INITIALISATION",
            "more_solar_possible": False,
            "max_solar_reached": False,
            "pv_at_limit": False,
        }
        self.last_grid_frame_id = 0
        self.last_grid_frame_at: datetime | None = None

    def publish_ems_intent(
        self,
        *,
        source: str,
        action: str,
        delta_w: float,
        now: datetime,
        **metadata: Any,
    ) -> None:
        self.last_ems_intent = EnergyIntent(
            source=source,
            action=action,
            delta_w=float(delta_w),
            created_at=now,
            metadata=dict(metadata),
        )

    def publish_inverter_state(self, **state: Any) -> None:
        self.inverter_state.update(state)

    def on_grid_frame(self, frame_id: int, now: datetime) -> None:
        self.last_grid_frame_id = int(frame_id)
        self.last_grid_frame_at = now

    def view(self) -> dict[str, Any]:
        intent = self.last_ems_intent
        return {
            "last_grid_frame_id": self.last_grid_frame_id,
            "last_grid_frame_at": self.last_grid_frame_at,
            "ems_intent": None if intent is None else {
                "source": intent.source,
                "action": intent.action,
                "delta_w": intent.delta_w,
                "created_at": intent.created_at,
                "metadata": dict(intent.metadata),
            },
            "inverter": dict(self.inverter_state),
        }
