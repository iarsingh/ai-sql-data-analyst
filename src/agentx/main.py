from agentx.ops import router as ops_router
from fastapi import FastAPI, HTTPException
from agentx.agent import run
app = FastAPI()
app.include_router(ops_router, prefix="/v1")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/agent/run")
def post_run(body: dict):
    try:
        return run(body.get("goal"), body.get("payload") or {})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
