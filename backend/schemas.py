from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class ExtractedStandard(BaseModel):
    standard_number: str
    standard_name: str

class CheckResult(BaseModel):
    id: int
    input_number: str
    input_name: str
    matched_number: Optional[str]
    matched_name: Optional[str]
    status: str
    matched_percentage: float
    message: str

class ValidateRequest(BaseModel):
    text: str
    online: bool = False

class ValidateResponse(BaseModel):
    results: List[CheckResult]

class StandardCreate(BaseModel):
    standard_number: str
    standard_name: str
    status: str = "现行"
    release_date: Optional[str] = None
    implement_date: Optional[str] = None
    abolish_date: Optional[str] = None
    replace_by: Optional[str] = None
    source: Optional[str] = None

class StandardResponse(BaseModel):
    id: int
    standard_number: str
    standard_name: str
    status: str
    release_date: Optional[date] = None
    implement_date: Optional[date] = None
    abolish_date: Optional[date] = None
    replace_by: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

class PaginatedResponse(BaseModel):
    total: int
    items: List[StandardResponse]
    skip: int
    limit: int