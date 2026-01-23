from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str
    brandfolder_id: Optional[str] = None

class IngestRequest(BaseModel):
    brandfolder_id: Optional[str] = None
    topic: Optional[str] = None
    max_assets: int = 50
    auto_transcribe: bool = False
