"""Map guest ticket types to department names (property must have matching department)."""

TICKET_TYPE_DEPARTMENT: dict[str, str] = {
    "complaint": "Reception",
    "service_request": "Reception",
    "housekeeping": "Housekeeping",
    "maintenance": "Maintenance",
    "feedback": "Reception",
    "emergency": "Security",
    "food": "Kitchen",
}
