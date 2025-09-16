
from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import Optional

class VoterCreate(BaseModel):
    voter_id: str = Field(..., description="Unique ID for the voter")
    name: str
    age: int = Field(..., ge=0)
    district: Optional[str] = None

    @validator("age")
    def age_minimum(cls, v):
        if v < 18:
            raise ValueError("Voter must be at least 18 years old")
        return v

class VoterUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0)
    district: Optional[str] = None

    @validator("age")
    def age_minimum_optional(cls, v):
        if v is not None and v < 18:
            raise ValueError("Voter must be at least 18 years old")
        return v

class VoterOut(BaseModel):
    voter_id: str
    name: str
    age: int
    district: Optional[str] = None
