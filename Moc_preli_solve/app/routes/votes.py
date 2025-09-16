
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
from ..data_store import store
from ..models.vote import VoteCreate, EncryptedBallot, TallyRequest, TimeRangeQuery, DPAnalyticsRequest, RCVSchulzeRequest
from ..services import encryption

router = APIRouter(prefix="/api/votes", tags=["Votes"])

def _now_iso():
    return datetime.utcnow().isoformat()

@router.post("", status_code=218, summary="Cast a vote (prevents duplicate voting)")
def cast_vote(v: VoteCreate):
    with store._lock:
        if v.voter_id not in store.voters:
            raise HTTPException(status_code=404, detail="Voter does not exist")
        if v.candidate_id not in store.candidates:
            raise HTTPException(status_code=404, detail="Candidate does not exist")
        # duplicate prevention: a voter may only cast one standard vote
        if any(x.get("voter_id")==v.voter_id and not x.get("weighted", False) for x in store.votes):
            raise HTTPException(status_code=409, detail="Duplicate vote from this voter")
        payload = v.dict()
        payload["timestamp"] = (v.timestamp or datetime.utcnow()).isoformat()
        payload["weighted"] = False
        store.votes.append(payload)
        return {"detail": "vote accepted", "ts": payload["timestamp"]}

@router.post("/weighted", status_code=218, summary="Cast a weighted vote")
def cast_weighted_vote(v: VoteCreate):
    with store._lock:
        if v.voter_id not in store.voters:
            raise HTTPException(status_code=404, detail="Voter does not exist")
        if v.candidate_id not in store.candidates:
            raise HTTPException(status_code=404, detail="Candidate does not exist")
        if v.weight is None or v.weight <= 0:
            raise HTTPException(status_code=422, detail="Weight must be > 0")
        payload = v.dict()
        payload["timestamp"] = (v.timestamp or datetime.utcnow()).isoformat()
        payload["weighted"] = True
        store.votes.append(payload)
        return {"detail": "weighted vote accepted", "ts": payload["timestamp"]}

@router.get("", status_code=222, summary="Retrieve votes within a time range")
def get_votes_in_range(start: Optional[datetime] = Query(None), end: Optional[datetime] = Query(None)):
    with store._lock:
        def in_range(ts):
            t = datetime.fromisoformat(ts)
            if start and t < start: return False
            if end and t > end: return False
            return True
        items = [v for v in store.votes if in_range(v["timestamp"])]
        return {"count": len(items), "votes": items}

@router.get("/summary", summary="Vote totals per candidate")
def vote_summary():
    with store._lock:
        totals: Dict[str, float] = {cid: 0.0 for cid in store.candidates}
        for v in store.votes:
            w = float(v.get("weight", 1.0)) if v.get("weighted") else 1.0
            cid = v["candidate_id"]
            if cid in totals:
                totals[cid] += w
        leaderboard = sorted(
            [{"candidate_id": cid, "votes": totals[cid]} for cid in totals],
            key=lambda x: (-x["votes"], x["candidate_id"]),
        )
        return {"leaderboard": leaderboard}

# Encrypted ballots & homomorphic tally
@router.post("/encrypted", summary="Submit an encrypted ballot with ZKP verification")
def submit_encrypted_ballot(b: EncryptedBallot):
    with store._lock:
        if b.voter_id not in store.voters:
            raise HTTPException(status_code=404, detail="Voter does not exist")
        if not encryption.verify_zkp(b.ciphertext, b.proof, b.voter_id):
            raise HTTPException(status_code=400, detail="Invalid zero-knowledge proof")
        store.encrypted_ballots.append(b.dict())
        return {"detail": "encrypted ballot accepted", "index": len(store.encrypted_ballots)-1}

@router.post("/homomorphic_tally", summary="Homomorphic tally for verifiable decryption")
def homomorphic_tally(req: TallyRequest):
    total_c = encryption.homomorphic_add(req.ciphertexts)
    decrypted = None
    if req.secret:
        decrypted = encryption.decrypt_ciphertext(total_c, req.secret)
    return {"combined_ciphertext": total_c, "decrypted_sum_mod_p": decrypted}

# Risk-Limiting Audit (Kaplan-Markov)
@router.post("/rla/kaplan_markov", summary="Compute Kaplan-Markov P-value")
def kaplan_markov(sampled_winner_votes: int, sampled_loser_votes: int, reported_margin: float):
    """
    A toy Kaplan-Markov calculation:
    p = min(1, exp(-2 * n * m^2)) where n is sample size, m is margin fraction.
    This is NOT production-grade; it's illustrative.
    """
    n = sampled_winner_votes + sampled_loser_votes
    if n <= 0 or reported_margin <= 0:
        raise HTTPException(status_code=422, detail="n and margin must be > 0")
    import math
    m = reported_margin
    p_value = min(1.0, math.exp(-2.0 * n * (m ** 2)))
    return {"n": n, "reported_margin": m, "p_value": p_value}

# Differential Privacy Analytics
@router.post("/analytics/dp", summary="Differential privacy analytics (Laplace mechanism)")
def dp_analytics(req: DPAnalyticsRequest):
    import random
    def laplace(scale: float):
        # Inverse CDF for Laplace(0, scale)
        u = random.random() - 0.5
        return -scale * (1 if u < 0 else -1) * math.log(1 - 2*abs(u))

    import math
    with store._lock:
        if req.metric == "turnout":
            count = len({v["voter_id"] for v in store.votes})
            noisy = count + laplace(req.sensitivity / req.epsilon)
            return {"metric": "turnout", "value": noisy}
        elif req.metric == "per_candidate":
            totals = {cid: 0.0 for cid in store.candidates}
            for v in store.votes:
                w = float(v.get("weight", 1.0)) if v.get("weighted") else 1.0
                cid = v["candidate_id"]
                if cid in totals:
                    totals[cid] += w
            noisy = {cid: val + laplace(req.sensitivity / req.epsilon) for cid, val in totals.items()}
            return {"metric": "per_candidate", "value": noisy}
        else:
            raise HTTPException(status_code=422, detail="Unknown metric")

# Ranked Choice Voting (Schulze method)
@router.post("/rcv/schulze", summary="Compute Schulze winners from ranked ballots")
def schulze(req: RCVSchulzeRequest):
    C = req.candidates
    idx = {c:i for i,c in enumerate(C)}
    n = len(C)
    # d[a][b] = number of voters who prefer a over b
    d = [[0]*n for _ in range(n)]
    for ballot in req.ballots:
        # build rank index for the ballot
        rank = {cand: i for i, cand in enumerate(ballot)}
        for a in C:
            for b in C:
                if a==b: continue
                if rank.get(a, 10**9) < rank.get(b, 10**9):
                    d[idx[a]][idx[b]] += 1
    # p[a][b] = strength of strongest path from a to b
    p = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i!=j:
                if d[i][j] > d[j][i]:
                    p[i][j] = d[i][j]
    for i in range(n):
        for j in range(n):
            if i==j: continue
            for k in range(n):
                if i==k or j==k: continue
                p[j][k] = max(p[j][k], min(p[j][i], p[i][k]))
    # winners where for all other j, p[i][j] >= p[j][i]
    winners = [C[i] for i in range(n) if all(p[i][j] >= p[j][i] for j in range(n) if i!=j)]
    return {"winners": winners, "matrix": p}
