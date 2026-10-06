THREAT_RULES = {
    "Drone": {"base": 3},
    "Helicopter": {"base": 2},
    "Airplane": {"base": 1},
    "Bird": {"base": 0},
}

def calculate_threat_level(class_name: str, confidence: float) -> str:
    base = THREAT_RULES.get(class_name, {"base": 1})["base"]

    if base == 0:
        return "none"
    if confidence >= 0.8:
        score = base + 1
    elif confidence >= 0.5:
        score = base
    else:
        score = max(base - 1, 0)

    if score >= 3:
        return "critical"
    elif score == 2:
        return "high"
    elif score == 1:
        return "medium"
    return "low"