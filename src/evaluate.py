import json
import glob
import os

from ollama import chat
from reader import extract_document


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


def document_to_text(document_data):
    """Convert reader output into plain text."""

    document_text = ""

    # Paragraphs
    for paragraph in document_data["paragraphs"]:
        document_text += paragraph + "\n"

    # Tables
    for table in document_data["tables"]:
        for row in table:
            document_text += " | ".join(row) + "\n"

    return document_text


def extract_with_qwen(document_text):
    """Send document text to Qwen and return JSON."""

    prompt = f"""
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

    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    response_text = response.message.content.strip()

    # Convert Qwen's response into Python dictionary
    return json.loads(response_text)


def load_label(label_path):
    """Load ground-truth JSON."""

    with open(label_path, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_document(document_path, label_path):

    document_name = os.path.basename(document_path)

    print(f"\n===== {document_name} =====")

    # Read DOCX
    document_data = extract_document(document_path)

    # Convert to text
    document_text = document_to_text(document_data)

    # Get Qwen prediction
    prediction = extract_with_qwen(document_text)

    # Load correct answer
    ground_truth = load_label(label_path)

    correct = 0

    for field in FIELDS:

        expected = ground_truth.get(field)
        predicted = prediction.get(field)

        if expected == predicted:
            print(f"{field:20} ✅")
            correct += 1
        else:
            print(f"{field:20} ❌")
            print(f"    Expected : {expected}")
            print(f"    Predicted: {predicted}")

    accuracy = correct / len(FIELDS) * 100

    print(f"\nAccuracy: {correct}/{len(FIELDS)} = {accuracy:.2f}%")

    return correct, len(FIELDS)


def main():

    document_files = sorted(
        glob.glob("data/court_document_dataset/documents/*.docx")
    )

    total_correct = 0
    total_fields = 0

    for document_path in document_files:

        document_name = os.path.splitext(
            os.path.basename(document_path)
        )[0]

        label_path = (
            f"data/court_document_dataset/labels/{document_name}.json"
        )

        if not os.path.exists(label_path):
            print(f"Missing label: {label_path}")
            continue

        correct, total = evaluate_document(
            document_path,
            label_path
        )

        total_correct += correct
        total_fields += total

    print("\n==============================")
    print("OVERALL RESULTS")
    print("==============================")

    overall_accuracy = total_correct / total_fields * 100

    print(
        f"Overall accuracy: "
        f"{total_correct}/{total_fields} "
        f"= {overall_accuracy:.2f}%"
    )


if __name__ == "__main__":
    main()