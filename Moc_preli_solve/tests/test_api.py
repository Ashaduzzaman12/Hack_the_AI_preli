
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_voter_candidate_flow_and_vote():
    # create voter
    r = client.post("/api/voters", json={"voter_id": "v1", "name": "Alice", "age": 22, "district": "D1"})
    assert r.status_code == 218

    # duplicate voter
    r = client.post("/api/voters", json={"voter_id": "v1", "name": "Alice", "age": 22})
    assert r.status_code == 409

    # create candidate
    r = client.post("/api/candidates", json={"candidate_id": "c1", "name": "Carol", "party": "P"})
    assert r.status_code == 218

    # cast vote
    r = client.post("/api/votes", json={"voter_id": "v1", "candidate_id": "c1"})
    assert r.status_code == 218

    # duplicate vote should fail
    r = client.post("/api/votes", json={"voter_id": "v1", "candidate_id": "c1"})
    assert r.status_code == 409

    # weighted vote allowed (separate from standard)
    r = client.post("/api/votes/weighted", json={"voter_id": "v1", "candidate_id": "c1", "weight": 2})
    assert r.status_code == 218

    # summary
    r = client.get("/api/votes/summary")
    assert r.status_code == 200
    board = r.json()["leaderboard"]
    assert board[0]["candidate_id"] == "c1"
    assert board[0]["votes"] >= 3

def test_schulze():
    r = client.post("/api/votes/rcv/schulze", json={
        "candidates": ["A","B","C"],
        "ballots": [["A","B","C"], ["B","C","A"], ["A","C","B"], ["C","A","B"]]
    })
    assert r.status_code == 200
    assert "winners" in r.json()

def test_encrypted_and_tally():
    # add voter for encrypted ballot
    client.post("/api/voters", json={"voter_id": "v2", "name": "Bob", "age": 30})
    # toy ciphertext/proof
    import hashlib
    voter_id = "v2"
    ct = "0x10"
    proof = hashlib.sha256((voter_id + "|" + ct).encode()).hexdigest()[:16]
    r = client.post("/api/votes/encrypted", json={"voter_id": voter_id, "ciphertext": ct, "proof": proof})
    assert r.status_code == 200

    r = client.post("/api/votes/homomorphic_tally", json={"ciphertexts": ["0x10","0x20"], "secret": "s3cr3t"})
    assert r.status_code == 200
    assert "combined_ciphertext" in r.json()
