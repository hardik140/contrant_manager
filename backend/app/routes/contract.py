from fastapi import APIRouter, UploadFile, File
from app.services.file_utils import extract_text
from app.services.gemini import summarize_contract
from app.database import db
import tempfile

router = APIRouter()

@router.post("/upload-contract/")
async def upload_contract(file: UploadFile = File(...)):
    ext = file.filename.split('.')[-1]
    if ext not in ["pdf", "docx"]:
        return {"error": "Unsupported file format"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(await file.read())
        file_path = tmp.name

    content = extract_text(file_path)
    summary = summarize_contract(content)

    doc_id = db.contracts.insert_one({
        "filename": file.filename,
        "content": content,
        "summary": summary,
        "type": "contract"
    }).inserted_id

    return {"id": str(doc_id), "summary": summary}
