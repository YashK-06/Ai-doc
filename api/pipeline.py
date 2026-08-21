import io
import json
import os
import re
import sys
from pathlib import Path

# Make the existing pipeline modules in src/ importable
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ollama import chat, list as ollama_list  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from normalize import normalize  # noqa: E402
from reader import extract_document  # noqa: E402
from validate import validate  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data" / "court_document_dataset"

# Load api/.env for overrides like OLLAMA_MODEL
load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def installed_model_names():
    """Names of models available in Ollama.

    Returns None when Ollama itself is unreachable,
    or a list (possibly empty) of installed model names.
    """

    try:
        response = ollama_list()
    except Exception:
        return None

    names = []

    for entry in getattr(response, "models", None) or []:
        name = getattr(entry, "model", None) or getattr(entry, "name", None)
        if isinstance(entry, dict):
            name = entry.get("model") or entry.get("name")
        if name:
            names.append(name)

    return names


def resolve_model() -> tuple[str, bool]:
    """Pick the model to use for extraction.

    Prefers the configured MODEL when it is installed.
    Falls back to any other installed model so the app keeps working.
    Returns (model_name, configured_model_is_ready).
    """

    installed = installed_model_names()

    if not installed:
        # Ollama down or nothing installed — let the call fail with a clear error
        return MODEL, False

    if MODEL in installed:
        return MODEL, True

    return sorted(installed)[0], False


def model_status() -> dict:
    """Full picture of model availability for the health endpoint."""

    installed = installed_model_names()
    ollama_ok = installed is not None
    installed = installed or []

    ready = MODEL in installed

    if ready:
        used = MODEL
    elif installed:
        used = sorted(installed)[0]
    else:
        used = None

    if ready:
        hint = None
    elif not ollama_ok:
        hint = "Ollama is not reachable — is it running?"
    else:
        hint = f"run: ollama pull {MODEL}"

    return {
        "model_configured": MODEL,
        "model_ready": ready,
        "model_used": used,
        "installed_models": installed,
        "ollama_ok": ollama_ok,
        "hint": hint,
    }

FIELDS = [
    "applicant_name",
    "case_number",
    "respondent_name",
    "lawyer_name",
    "court_name",
    "case_type",
    "filing_date",
    "address"
]

PROMPT_TEMPLATE = """
Extract the following fields from the document:

- applicant_name
- case_number
- respondent_name
- lawyer_name
- court_name
- case_type
- filing_date
- address

Rules:
1. Return only valid JSON.
2. Use exactly the field names above.
3. If a field is not present, return null.
4. Do not guess or invent information.
5. Return all fields.

Document:
{document_text}
"""


def document_to_text(document_data: dict) -> str:
    """Convert reader output into plain text."""

    document_text = ""

    for paragraph in document_data["paragraphs"]:
        document_text += paragraph + "\n"

    for table in document_data["tables"]:
        for row in table:
            document_text += " | ".join(row) + "\n"

    return document_text


def parse_llm_json(response_text: str) -> dict:
    """Parse a JSON object out of a raw LLM response.

    Handles markdown code fences and stray text around the object,
    which Qwen sometimes adds despite instructions.
    """

    text = response_text.strip()

    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")

    return json.loads(text[start:end + 1])


def extract_fields(document_text: str) -> dict:
    """Send document text to the local model and return parsed JSON."""

    model, _ = resolve_model()

    prompt = PROMPT_TEMPLATE.format(document_text=document_text)

    response = chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return parse_llm_json(response.message.content)


def run_extraction(source) -> tuple[dict, list]:
    """Run the full pipeline on a .docx path or file-like object.

    Returns (prediction_with_warnings, warnings).
    """

    document_data = extract_document(source)

    document_text = document_to_text(document_data)

    prediction = extract_fields(document_text)

    prediction = normalize(prediction)
    prediction, warnings = validate(prediction)

    return prediction, warnings


def compare_with_label(prediction: dict, label: dict) -> dict:
    """Compare prediction against ground truth field by field."""

    results = []
    passed = 0

    for field in FIELDS:

        expected = label.get(field)
        predicted = prediction.get(field)
        match = expected == predicted

        if match:
            passed += 1

        results.append(
            {
                "field": field,
                "expected": expected,
                "predicted": predicted,
                "match": match
            }
        )

    total = len(FIELDS)
    accuracy = passed / total * 100

    return {
        "results": results,
        "passed": passed,
        "total": total,
        "accuracy": accuracy
    }


def load_label(name: str):
    """Load ground-truth JSON for a document, or None if missing."""

    label_path = DATASET_DIR / "labels" / f"{name}.json"

    if not label_path.exists():
        return None

    return json.loads(label_path.read_text(encoding="utf-8"))


def save_output(name: str, data: dict) -> str:
    """Save extraction result to the output folder."""

    output_dir = DATASET_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{name}.json"

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return str(output_path)


def docx_source(file_bytes=None, name: str = None):
    """Return a source usable by extract_document (path or BytesIO)."""

    if file_bytes is not None:
        return io.BytesIO(file_bytes)

    return DATASET_DIR / "documents" / f"{name}.docx"
