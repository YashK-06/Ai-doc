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

KNOWN_CASE_TYPES = {
    "Civil", "Criminal", "Family", "Commercial",
    "Labour", "Contract", "Property"
}


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

    case_type = data.get("case_type")
    if case_type and case_type not in KNOWN_CASE_TYPES:
        warnings.append(f"Unknown case type: {case_type}")

    lawyer = data.get("lawyer_name")
    if lawyer and not lawyer.startswith("Adv."):
        warnings.append(f"Lawyer name missing Adv. prefix: {lawyer}")

    for name_field in ["applicant_name", "respondent_name"]:
        name = data.get(name_field)
        if name and re.search(r"\d", name):
            warnings.append(f"Name contains numbers: {name_field} = {name}")

    court = data.get("court_name")
    if court and "court" not in court.lower():
        warnings.append(f"Court name missing 'Court': {court}")

    if warnings:
        data["warnings"] = warnings

    return data, warnings
