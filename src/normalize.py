import re


STRING_FIELDS = [
    "applicant_name",
    "respondent_name",
    "lawyer_name",
    "court_name",
    "address"
]

CASE_TYPE_MAP = {
    "civil": "Civil",
    "civil case": "Civil",
    "civil dispute": "Civil",

    "criminal": "Criminal",
    "criminal case": "Criminal",

    "family": "Family",
    "family case": "Family",

    "commercial": "Commercial",
    "commercial case": "Commercial",

    "labour": "Labour",
    "labour case": "Labour",

    "contract": "Contract",
    "contract matter": "Contract",

    "property": "Property",
    "property case": "Property"
}

def normalize(data: dict) -> dict:
    """Clean and standardize extracted fields."""

    result = {}

    for key, value in data.items():

        if key == "warnings":
            result[key] = value
            continue

        if value is None:
            result[key] = None
            continue

        if not isinstance(value, str):
            result[key] = value
            continue

        value = value.strip()

        if value == "":
            result[key] = None
            continue

        if key == "filing_date":
            value = normalize_date(value)

        elif key == "case_number":
            value = value.upper()

        elif key == "case_type":
            value = normalize_case_type(value)

        elif key == "lawyer_name":
            value = re.sub(r"\s+", " ", value)
            if not value.startswith("Adv."):
                value = "Adv. " + value

        elif key in STRING_FIELDS:
            value = re.sub(r"\s+", " ", value)

        result[key] = value

    return result

def normalize_case_type(value: str) -> str:
    """Convert case-type variations into a standard value."""

    normalized = value.strip().lower()

    return CASE_TYPE_MAP.get(
        normalized,
        value.title()
    )


def normalize_date(date_str: str) -> str:
    """Try to parse various date formats into YYYY-MM-DD."""

    date_str = date_str.strip()

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }

    match = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", date_str)
    if match:
        day, month_name, year = match.groups()
        month = month_map.get(month_name.lower()[:3])
        if month:
            return f"{year}-{month}-{day.zfill(2)}"

    return date_str
