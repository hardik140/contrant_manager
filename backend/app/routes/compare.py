from fastapi import APIRouter, UploadFile, File
from app.services.file_utils import extract_text
from app.services.gemini import compare_with_policy
from app.database import db
import tempfile

router = APIRouter()

@router.post("/compare/")
async def compare_contract_policy(contract: UploadFile = File(...), policy: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp2:
        tmp1.write(await contract.read())
        tmp2.write(await policy.read())

    contract_text = extract_text(tmp1.name)
    policy_text = extract_text(tmp2.name)

    comparison_result = compare_with_policy(contract_text, policy_text)

    db.comparisons.insert_one({
        "contract": contract.filename,
        "policy": policy.filename,
        "contract_text": contract_text,
        "policy_text": policy_text,
        "result": comparison_result,
        "type": "comparison"
    })

    return {"comparison": comparison_result}
