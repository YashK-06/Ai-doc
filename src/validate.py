import re


REQUIRED_FIELDS = [
    "applicant_name",
    "case_number",
    "respondent_name",
    "lawyer_name",
    "court_name",
    "case_type",
    "filing_date",
    "address"
]


def validate(data: dict) -> tuple[dict, list[str]]:
    """Validate extracted fields. Returns (data_with_warnings, warnings)."""

    warnings = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            warnings.append(f"Missing field: {field}")

    for field in REQUIRED_FIELDS:
        if data.get(field) is None:
            warnings.append(f"Null value: {field}")

    date = data.get("filing_date")
    if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        warnings.append(f"Invalid date format: {date}")

    case_number = data.get("case_number")
    if case_number and not re.match(r"^[A-Z]+-\d{4}-\d{4}$", case_number):
        warnings.append(f"Invalid case number format: {case_number}")

    if warnings:
        data["warnings"] = warnings

    return data, warnings
