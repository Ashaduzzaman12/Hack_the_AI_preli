
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class CandidateCreate(BaseModel):
    candidate_id: str = Field(..., description="Unique ID for the candidate")
    name: str
    party: Optional[str] = None

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    party: Optional[str] = None

class CandidateOut(BaseModel):
    candidate_id: str
    name: str
    party: Optional[str] = None
