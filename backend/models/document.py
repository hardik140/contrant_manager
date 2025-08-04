from pydantic import BaseModel
from typing import Optional
from bson import ObjectId

class Document(BaseModel):
    id: Optional[str]
    filename: str
    content: str
    summary: Optional[str] = None
    type: str  # "contract" or "comparison"
