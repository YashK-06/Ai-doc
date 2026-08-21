import json
import os
import glob
from pathlib import Path

from dotenv import load_dotenv

import ollama

from reader import extract_document
from normalize import normalize
from validate import validate
from database import get_collection


# Load src/.env (MONGODB_URI, optional OLLAMA_MODEL)
load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def installed_model_names():
    """Names of models available in Ollama, or None if unreachable."""

    try:
        response = ollama.list()
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


def resolve_model():
    """Configured model if installed, otherwise any installed model."""

    installed = installed_model_names()

    if not installed:
        # Ollama down or nothing installed — let the call fail with a clear error
        return MODEL

    if MODEL in installed:
        return MODEL

    fallback = sorted(installed)[0]
    print(f"'{MODEL}' is not installed, falling back to '{fallback}'")

    return fallback


def extract_with_qwen(document_data):
    """Extract required fields from a document using Qwen."""

    text_parts = []

    # Add paragraphs
    for paragraph in document_data["paragraphs"]:
        text_parts.append(paragraph)

    # Add tables
    for table in document_data["tables"]:
        for row in table:
            text_parts.append(" | ".join(row))

    document_text = "\n".join(text_parts)

    prompt = f"""
Extract the following fields from this court document.

Return ONLY valid JSON.

Required fields:
- applicant_name
- case_number
- respondent_name
- lawyer_name
- court_name
- case_type
- filing_date
- address

Important:
- Extract the actual applicant, not the respondent.
- Preserve the complete lawyer name.
- Preserve the complete court name.
- Return only the case type such as Civil, Criminal, Family,
  Commercial, Labour, Contract, or Property.
- Return the filing date exactly as found.
- If a field cannot be found, use null.

Document:
{document_text}
"""

    response = ollama.chat(
        model=resolve_model(),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response["message"]["content"].strip()

    # Remove markdown code fences if Qwen adds them
    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model did not return valid JSON: {exc}. "
            f"Response started with: {content[:200]!r}"
        )


def process_document(file_path):
    """DOCX → Qwen → normalize → validate → MongoDB."""

    print(f"\nProcessing: {file_path}")

    # 1. Read DOCX
    document_data = extract_document(file_path)

    # 2. Extract fields using Qwen
    extracted_data = extract_with_qwen(document_data)

    print("Qwen extraction complete.")

    # 3. Normalize extracted data
    normalized_data = normalize(extracted_data)

    print("Normalization complete.")

    # 4. Validate data
    validated_data, warnings = validate(normalized_data)

    print("Validation complete.")

    # 5. Add source document
    validated_data["source_document"] = os.path.basename(file_path)

    # 6. Save to MongoDB (upsert: re-runs update instead of duplicating)
    result = get_collection().replace_one(
        {"source_document": os.path.basename(file_path)},
        validated_data,
        upsert=True
    )

    if result.upserted_id:
        print(f"Saved to MongoDB: {result.upserted_id}")
    else:
        print("Updated existing record in MongoDB.")

    # 7. Display warnings if any
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    return validated_data


if __name__ == "__main__":

    documents_path = (
        BASE_DIR / "data" / "court_document_dataset" / "documents"
    )

    files = sorted(
        glob.glob(str(documents_path / "*.docx"))
    )

    print(f"Found {len(files)} documents.")

    for file_path in files:

        try:
            process_document(file_path)

        except Exception as e:
            print(f"ERROR processing {file_path}: {e}")
