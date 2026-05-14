"""
Hotel CCTV / AI surveillance: unwanted scenarios checklist + timer-based rules.

Timer rules: when a condition persists longer than `default_threshold_seconds`, raise an event
(e.g. guard absent from gate > 180s).
"""
from typing import Any, List, TypedDict


class HotelScenario(TypedDict):
    code: str
    label: str
    category: str
    default_severity: str
    is_timer_based: bool
    default_threshold_seconds: int | None
    root_cause_hint: str
    description: str


HOTEL_SURVEILLANCE_SCENARIOS: List[HotelScenario] = [
    {
        "code": "guard_absence_gate",
        "label": "Guard / reception unmanned (gate or lobby)",
        "category": "security",
        "default_severity": "high",
        "is_timer_based": True,
        "default_threshold_seconds": 180,
        "root_cause_hint": "Staffing gap, break overlap, or unauthorized absence",
        "description": "No staff detected at monitored gate/lobby desk for longer than threshold.",
    },
    {
        "code": "unauthorized_loitering_back_of_house",
        "label": "Unauthorized person in back-of-house / staff-only zone",
        "category": "security",
        "default_severity": "critical",
        "is_timer_based": False,
        "default_threshold_seconds": None,
        "root_cause_hint": "Tailgating, lost guest, or intruder",
        "description": "Person in kitchen, laundry, or inventory corridors without staff badge/uniform heuristics.",
    },
    {
        "code": "kitchen_hygiene_violation",
        "label": "Kitchen hygiene breach (no hairnet / glove)",
        "category": "f_b",
        "default_severity": "medium",
        "is_timer_based": False,
        "default_threshold_seconds": None,
        "root_cause_hint": "Training gap or rush-hour corner-cutting",
        "description": "Food prep area policy violations detectable by vision models.",
    },
    {
        "code": "pool_area_unsupervised_child",
        "label": "Pool / gym minor unsupervised (policy)",
        "category": "safety",
        "default_severity": "high",
        "is_timer_based": True,
        "default_threshold_seconds": 60,
        "root_cause_hint": "Lifeguard sightline blocked or policy breach",
        "description": "Timer: child in pool zone without adult proximity for > threshold.",
    },
    {
        "code": "corridor_obstruction_emergency",
        "label": "Emergency route blocked (cart / linen)",
        "category": "safety",
        "default_severity": "high",
        "is_timer_based": True,
        "default_threshold_seconds": 120,
        "root_cause_hint": "Housekeeping workflow or storage overflow",
        "description": "Obstruction persists in fire-exit corridor beyond threshold.",
    },
    {
        "code": "cashier_drawer_open_extended",
        "label": "POS / front desk drawer open unusually long",
        "category": "fraud",
        "default_severity": "medium",
        "is_timer_based": True,
        "default_threshold_seconds": 300,
        "root_cause_hint": "Procedure violation or collusion risk",
        "description": "Drawer open state exceeds configured seconds during staffed hours.",
    },
    {
        "code": "after_hours_movement_restricted_floor",
        "label": "After-hours movement on restricted floor",
        "category": "security",
        "default_severity": "high",
        "is_timer_based": False,
        "default_threshold_seconds": None,
        "root_cause_hint": "Wrong-floor access or tailgating",
        "description": "Motion/person detection outside configured quiet hours.",
    },
    {
        "code": "parking_perimeter_breach",
        "label": "Vehicle / person at perimeter fence (unusual)",
        "category": "security",
        "default_severity": "medium",
        "is_timer_based": False,
        "default_threshold_seconds": None,
        "root_cause_hint": "Delivery exception or trespass",
        "description": "Perimeter camera anomaly classification.",
    },
    {
        "code": "garbage_overflow_service_yard",
        "label": "Garbage / loading dock overflow",
        "category": "operations",
        "default_severity": "low",
        "is_timer_based": True,
        "default_threshold_seconds": 600,
        "root_cause_hint": "Waste vendor SLA miss or peak occupancy",
        "description": "Overflow condition sustained beyond threshold.",
    },
    {
        "code": "violence_or_distress_cluster",
        "label": "Aggressive interaction / crowd distress (lobby or bar)",
        "category": "safety",
        "default_severity": "critical",
        "is_timer_based": False,
        "default_threshold_seconds": None,
        "root_cause_hint": "Incident escalation — security dispatch",
        "description": "Audio-visual distress heuristics; integrate with on-site response.",
    },
]


def default_scenario_rules_for_camera() -> List[dict[str, Any]]:
    """Per-camera enabled flags + thresholds (merge with PATCH)."""
    rules: List[dict[str, Any]] = []
    for s in HOTEL_SURVEILLANCE_SCENARIOS:
        rules.append(
            {
                "scenario_code": s["code"],
                "enabled": s["code"] in ("guard_absence_gate", "corridor_obstruction_emergency"),
                "threshold_seconds": s["default_threshold_seconds"],
            }
        )
    return rules
