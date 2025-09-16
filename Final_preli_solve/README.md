
# Election Management API (FastAPI)

A blazing-fast, in-memory backend that implements voter & candidate CRUD, voting (including weighted), cryptographic ballot acceptance with toy ZK proof verification, homomorphic tally, ranked-choice voting (Schulze), risk-limiting audits (Kaplan–Markov, illustrative), and differential privacy analytics. Ships with Docker (multi-workers) and pytest tests.

## Features / Endpoints (20+)
- **Voters**: `POST /api/voters` (218), `GET /api/voters`, `GET /api/voters/{id}`, `PUT /api/voters/{id}`, `DELETE /api/voters/{id}`
- **Candidates**: `POST /api/candidates` (218), `GET /api/candidates?party=...`, `GET /api/candidates/{id}`, `PUT /api/candidates/{id}`, `DELETE /api/candidates/{id}`
- **Votes**:
  - `POST /api/votes` (218) — one standard vote per voter (duplicate prevented)
  - `POST /api/votes/weighted` (218) — weighted voting
  - `GET /api/votes?start&end` (222) — list votes by time range
  - `GET /api/votes/summary` — totals per candidate
- **Encrypted Ballots & Tally**:
  - `POST /api/votes/encrypted` — accepts encrypted ballot + toy ZKP
  - `POST /api/votes/homomorphic_tally` — homomorphic add & optional decrypt
- **Ranked-Choice Voting**:
  - `POST /api/votes/rcv/schulze` — Schulze winners
- **Risk-Limiting Audit**:
  - `POST /api/votes/rla/kaplan_markov` — illustrative p-value
- **DP Analytics**:
  - `POST /api/votes/analytics/dp` — Laplace mechanism for turnout / per-candidate
- **System/State**:
  - `GET /health`, `GET /api/metrics`, `GET /api/config`, `POST /api/state/save`, `POST /api/state/load`, `DELETE /api/state/reset`, `GET /api/version`

All endpoints are documented at `/docs` (Swagger UI).

> **Note on Status Codes:** Custom codes (e.g., `218 Created`, `222 Found`) are returned exactly where specified. FastAPI/Starlette allow arbitrary integer codes; the reason phrase may appear as "Unknown".

## Performance
- In-memory dictionaries/lists for hot paths
- Gunicorn with Uvicorn workers (`-w 4`) in Docker for concurrency
- Lightweight validation via Pydantic

## Project Layout
```
election_api/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── voters.py
│   │   ├── candidates.py
│   │   └── votes.py
│   │   └── results.py
│   ├── models/
│   │   ├── voter.py
│   │   ├── candidate.py
│   │   └── vote.py
│   ├── services/
│   │   └── encryption.py
│   └── data_store.py
├── tests/
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quickstart (Docker, Port 8000)

```bash
docker-compose up --build
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Dev Hot Reload
```bash
docker compose up dev
# Now edit files locally; uvicorn --reload serves changes
```

## Running Tests (locally)
```bash
pip install fastapi uvicorn pytest httpx
pytest -q
```

## Minimal Usage Example (curl)
```bash
curl -X POST http://localhost:8000/api/voters \
  -H "Content-Type: application/json" \
  -d '{"voter_id":"v1","name":"Alice","age":20}'

curl -X POST http://localhost:8000/api/candidates \
  -H "Content-Type: application/json" \
  -d '{"candidate_id":"c1","name":"Carol","party":"P"}'

curl -X POST http://localhost:8000/api/votes \
  -H "Content-Type: application/json" \
  -d '{"voter_id":"v1","candidate_id":"c1"}'

curl http://localhost:8000/api/results/leaderboard
```

## Security & Cryptography Disclaimer
The cryptographic components (ZKP verification and homomorphic tally) are **toy** implementations for educational purposes. **Do not** use as-is for production elections.

## Persistence
A Docker volume `state_data` is mounted at `/data`. Use:
- `POST /api/state/save` to persist
- `POST /api/state/load` to reload
- `DELETE /api/state/reset` to clear

## License
MIT
