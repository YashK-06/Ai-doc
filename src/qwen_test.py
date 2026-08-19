from ollama import chat
from reader import extract_document


# Path to the Word document
file_path = "data/court_document_dataset/documents/court_001.docx"

# Read the document
document_data = extract_document(file_path)


# Convert the extracted document into text
document_text = ""

# Add paragraphs
for paragraph in document_data["paragraphs"]:
    document_text += paragraph + "\n"

# Add tables
for table in document_data["tables"]:
    for row in table:
        document_text += " | ".join(row) + "\n"


# Send document to Qwen
response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": f"""
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
3. If a field is not present in the document, return null.
4. Do not guess or invent information.
5. Return all fields, even when their value is null.

Document:
{document_text}
"""
        }
    ]
)












print("----- QWEN RESPONSE -----")
print(response.message.content)