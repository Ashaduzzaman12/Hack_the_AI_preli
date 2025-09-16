
from __future__ import annotations
from fastapi import APIRouter
from typing import Dict
from ..data_store import store

router = APIRouter(prefix="/api/results", tags=["Results"])

@router.get("/leaderboard", summary="Leaderboard sorted by votes")
def leaderboard():
    totals: Dict[str, float] = {cid: 0.0 for cid in store.candidates}
    for v in store.votes:
        w = float(v.get("weight", 1.0)) if v.get("weighted") else 1.0
        cid = v["candidate_id"]
        if cid in totals:
            totals[cid] += w
    board = sorted(
        [{"candidate_id": cid, "votes": totals[cid]} for cid in totals],
        key=lambda x: (-x["votes"], x["candidate_id"]),
    )
    return {"leaderboard": board}

@router.get("/winner", summary="Winner with tie handling")
def winner():
    board = leaderboard()["leaderboard"]
    if not board:
        return {"winner": None, "tie": False}
    top = board[0]["votes"]
    winners = [x["candidate_id"] for x in board if x["votes"] == top]
    return {"winner": winners[0] if len(winners)==1 else None, "tie": len(winners)>1, "tied": winners if len(winners)>1 else None}
