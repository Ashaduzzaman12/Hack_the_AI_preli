
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..data_store import store
from ..models.candidate import CandidateCreate, CandidateUpdate, CandidateOut

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@router.post("", response_model=CandidateOut, status_code=218, summary="Register a candidate")
def register_candidate(c: CandidateCreate):
    with store._lock:
        if c.candidate_id in store.candidates:
            raise HTTPException(status_code=409, detail="Duplicate candidate_id")
        store.candidates[c.candidate_id] = c.dict()
        return c

@router.get("", response_model=List[CandidateOut], summary="List candidates (filter by party)")
def list_candidates(party: Optional[str] = Query(None)):
    with store._lock:
        items = list(store.candidates.values())
        if party:
            items = [x for x in items if (x.get("party") or "") == party]
        return items

@router.get("/{candidate_id}", response_model=CandidateOut, summary="Get candidate by ID")
def get_candidate(candidate_id: str):
    with store._lock:
        c = store.candidates.get(candidate_id)
        if not c:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return c

@router.put("/{candidate_id}", response_model=CandidateOut, summary="Update candidate")
def update_candidate(candidate_id: str, upd: CandidateUpdate):
    with store._lock:
        c = store.candidates.get(candidate_id)
        if not c:
            raise HTTPException(status_code=404, detail="Candidate not found")
        data = c.copy()
        for k, val in upd.dict(exclude_unset=True).items():
            data[k] = val
        store.candidates[candidate_id] = data
        return data

@router.delete("/{candidate_id}", summary="Delete candidate")
def delete_candidate(candidate_id: str):
    with store._lock:
        if candidate_id not in store.candidates:
            raise HTTPException(status_code=404, detail="Candidate not found")
        del store.candidates[candidate_id]
        return {"detail": "deleted"}
