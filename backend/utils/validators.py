"""utils/validators.py — Input validation helpers"""

import re


def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 128:
        return False, "Password too long"
    return True, ""


def validate_prediction_input(data: dict) -> tuple[bool, str]:
    required = ['age', 'gender', 'bmi', 'smoking', 'genetic_risk',
                 'physical_activity', 'alcohol_intake', 'cancer_history', 'diagnosis']

    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    try:
        age = float(data['age'])
        if not (1 <= age <= 120):
            return False, "Age must be between 1 and 120"

        bmi = float(data['bmi'])
        if not (10 <= bmi <= 70):
            return False, "BMI must be between 10 and 70"

        gender = int(data['gender'])
        if gender not in (0, 1):
            return False, "Gender must be 0 (Female) or 1 (Male)"

        smoking = int(data['smoking'])
        if smoking not in (0, 1):
            return False, "Smoking must be 0 or 1"

        genetic_risk = int(data['genetic_risk'])
        if genetic_risk not in (0, 1, 2):
            return False, "Genetic risk must be 0, 1, or 2"

        pa = float(data['physical_activity'])
        if not (0 <= pa <= 24):
            return False, "Physical activity must be between 0 and 24 hours/week"

        alcohol = float(data['alcohol_intake'])
        if not (0 <= alcohol <= 50):
            return False, "Alcohol intake must be between 0 and 50 units/week"

    except (TypeError, ValueError) as e:
        return False, f"Invalid numeric value: {e}"

    return True, ""


def sanitize_string(s: str, max_length: int = 200) -> str:
    """Strip and truncate a string."""
    return str(s).strip()[:max_length] if s else ""
