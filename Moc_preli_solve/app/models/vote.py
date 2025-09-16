
from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class VoteCreate(BaseModel):
    voter_id: str
    candidate_id: str
    weight: Optional[float] = Field(1.0, ge=0.0)
    timestamp: Optional[datetime] = None

class EncryptedBallot(BaseModel):
    voter_id: str
    ciphertext: str
    proof: str  # zero-knowledge proof placeholder
    metadata: Optional[dict] = None

class TallyRequest(BaseModel):
    ciphertexts: List[str]
    secret: Optional[str] = None  # placeholder "key"

class TimeRangeQuery(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None

class DPAnalyticsRequest(BaseModel):
    metric: str = Field(..., description="one of: turnout, per_candidate")
    epsilon: float = Field(1.0, gt=0.0)
    sensitivity: float = Field(1.0, gt=0.0)

class RCVSchulzeRequest(BaseModel):
    candidates: List[str]
    ballots: List[List[str]]  # each ballot is ranking like ["A","C","B"]
