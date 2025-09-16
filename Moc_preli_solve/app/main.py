
from __future__ import annotations
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .data_store import store
from .routes import voters, candidates, votes, results

app = FastAPI(
    title="Election Management API",
    version="1.0.0",
    description="A blazing-fast, in-memory Election API with crypto & analytics features. See /docs",
    swagger_ui_parameters={"defaultModelsExpandDepth": 0},
)

# CORS permissive for demos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request metrics middleware
@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    store.metrics["requests"] += 1
    response.headers["X-Response-Time"] = str((time.perf_counter() - start) * 1000.0)
    return response

app.include_router(voters.router)
app.include_router(candidates.router)
app.include_router(votes.router)
app.include_router(results.router)

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}

@app.get("/api/metrics", tags=["System"])
def metrics():
    uptime = time.time() - store.metrics["start_time"]
    return {"requests": store.metrics["requests"], "uptime_sec": uptime}

@app.get("/api/config", tags=["System"])
def config():
    return {"persist_enabled": bool(store.persist_path), "persist_path": str(store.persist_path) if store.persist_path else None}

@app.post("/api/state/save", tags=["System"])
def save_state():
    store.save()
    return {"detail": "saved"}

@app.post("/api/state/load", tags=["System"])
def load_state():
    # re-init store (simple approach)
    from .data_store import InMemoryStore
    global store
    store = InMemoryStore(persist_path="/data/state.json")
    return {"detail": "loaded"}

@app.delete("/api/state/reset", tags=["System"])
def reset_state():
    store.reset()
    return {"detail": "reset"}

@app.get("/api/version", tags=["System"])
def version():
    return {"version": "1.0.0"}
