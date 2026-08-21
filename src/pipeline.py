import json
import os
import glob

from reader import extract_document
from normalize import normalize
from validate import validate
from database import collection

import ollama


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
        model="qwen3:8b",
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

    return json.loads(content)


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

    # 6. Save to MongoDB
    result = collection.insert_one(validated_data)

    print(f"Saved to MongoDB: {result.inserted_id}")

    # 7. Display warnings if any
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    return validated_data


if __name__ == "__main__":

    documents_path = "data/court_document_dataset/documents"

    files = glob.glob(
        os.path.join(documents_path, "*.docx")
    )

    print(f"Found {len(files)} documents.")

    for file_path in files:

        try:
            process_document(file_path)

        except Exception as e:
            print(f"ERROR processing {file_path}: {e}")