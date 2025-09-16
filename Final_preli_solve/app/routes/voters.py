
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from ..data_store import store
from ..models.voter import VoterCreate, VoterUpdate, VoterOut

router = APIRouter(prefix="/api/voters", tags=["Voters"])

@router.post("", response_model=VoterOut, status_code=218, summary="Register a voter")
def register_voter(v: VoterCreate):
    with store._lock:
        if v.voter_id in store.voters:
            raise HTTPException(status_code=409, detail="Duplicate voter_id")
        store.voters[v.voter_id] = v.dict()
        return v

@router.get("", response_model=List[VoterOut], summary="List voters")
def list_voters():
    with store._lock:
        return list(store.voters.values())

@router.get("/{voter_id}", response_model=VoterOut, summary="Get voter by ID")
def get_voter(voter_id: str):
    with store._lock:
        v = store.voters.get(voter_id)
        if not v:
            raise HTTPException(status_code=404, detail="Voter not found")
        return v

@router.put("/{voter_id}", response_model=VoterOut, summary="Update voter")
def update_voter(voter_id: str, upd: VoterUpdate):
    with store._lock:
        v = store.voters.get(voter_id)
        if not v:
            raise HTTPException(status_code=404, detail="Voter not found")
        data = v.copy()
        for k, val in upd.dict(exclude_unset=True).items():
            data[k] = val
        store.voters[voter_id] = data
        return data

@router.delete("/{voter_id}", status_code=200, summary="Delete voter")
def delete_voter(voter_id: str):
    with store._lock:
        if voter_id not in store.voters:
            raise HTTPException(status_code=404, detail="Voter not found")
        del store.voters[voter_id]
        return {"detail": "deleted"}
