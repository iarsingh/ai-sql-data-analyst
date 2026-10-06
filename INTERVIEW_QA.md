# ai-sql-data-analyst — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does ai-sql-data-analyst address, and what can you demonstrate?

Question → agent chooses profile/SQL/stats/viz tools → explanation. Writes refused.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/agentx/main.py`](src/agentx/main.py): Implementation or supporting configuration.
- [`src/agentx/ops.py`](src/agentx/ops.py): Implementation or supporting configuration.
- [`src/agentx/agent.py`](src/agentx/agent.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.
- [`tests/test_agent.py`](tests/test_agent.py): Executable checks and regression examples.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `run` and explain the decision it makes?

The main walkthrough here is `run(goal, payload)` in [`src/agentx/agent.py`](src/agentx/agent.py#L4).

```python
def run(goal, payload):
    if not goal or not str(goal).strip():
        raise ValueError("goal is empty")
    low = goal.lower()
    if any(w in low for w in WRITES):
        return {"refused": True, "reason": "destructive action requires a human", "applied": False, "tools": []}
    rows = payload.get("rows") or []; totals = {};
    for row in rows:
        totals[str(row.get("region","unknown"))] = totals.get(str(row.get("region","unknown")), 0) + float(row.get("revenue", 0))
    result = {"by_region": totals, "chart": list(totals)}
    return {"refused": False, "tools": TOOLS, "analysis": result, "applied": False, "needs_approval": False}
```

The implementation calls `ValueError`, `any`, `float`, `goal.lower`, `list`, `payload.get`, `row.get`, `str`, `str(goal).strip`. In an interview, trace those calls in execution order using a fixture input.

## 4. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `ValueError('goal is empty')` in [`src/agentx/agent.py`](src/agentx/agent.py#L6).
- `HTTPException(422, str(exc))` in [`src/agentx/main.py`](src/agentx/main.py#L16).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/agentx/ops.py`](src/agentx/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/agentx/ops.py`](src/agentx/ops.py#L100).
- `HTTPException(status_code=404, detail='job not found')` in [`src/agentx/ops.py`](src/agentx/ops.py#L109).
- `HTTPException(status_code=403, detail='production apply is disabled in this lab')` in [`src/agentx/ops.py`](src/agentx/ops.py#L113).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 5. Which test would you use to demonstrate correctness?

[`tests/test_agent.py`](tests/test_agent.py#L5) contains `test_run_and_refuse`:

```python
def test_run_and_refuse():
    payload = client.post("/agent/run", json={"goal": 'Why did revenue fall last month?', "payload": {'rows': [{'region': 'north', 'revenue': 10}, {'region': 'south', 'revenue': 30}]}}).json()
    assert payload["refused"] is False
    assert payload["applied"] is False
    assert payload["analysis"]["by_region"]["south"] == 30
    refused = client.post("/agent/run", json={"goal": 'delete old revenue rows'}).json()
    assert refused["refused"] is True
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 6. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/agentx/main.py`](src/agentx/main.py#L8).
- `POST /agent/run` → `post_run` in [`src/agentx/main.py`](src/agentx/main.py#L12).
- `GET /readyz` → `readyz` in [`src/agentx/ops.py`](src/agentx/ops.py#L74).
- `POST /workspaces` → `create_workspace` in [`src/agentx/ops.py`](src/agentx/ops.py#L80).
- `GET /workspaces` → `list_workspaces` in [`src/agentx/ops.py`](src/agentx/ops.py#L98).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/agentx/ops.py`](src/agentx/ops.py#L106).
- `GET /jobs/{job_id}` → `get_job` in [`src/agentx/ops.py`](src/agentx/ops.py#L130).
- `POST /jobs/{job_id}/approve` → `approve_job` in [`src/agentx/ops.py`](src/agentx/ops.py#L140).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 7. Where does state live, and what happens with multiple workers?

Module-level containers include `TOOLS` in [`src/agentx/agent.py`](src/agentx/agent.py); `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/agentx/ops.py`](src/agentx/ops.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 8. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 9. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 10. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 11. What is the input-to-output contract of `run`?

In [`src/agentx/agent.py`](src/agentx/agent.py#L4), `run(goal, payload)` receives the inputs. The function computes these intermediate values:

- `low = goal.lower()`
- `rows = payload.get('rows') or []`
- `totals = {}`
- `result = {'by_region': totals, 'chart': list(totals)}`

Its result is defined by:

- `{'refused': False, 'tools': TOOLS, 'analysis': result, 'applied': False, 'needs_approval': False}`
- `{'refused': True, 'reason': 'destructive action requires a human', 'applied': False, 'tools': []}`

## 12. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/agentx/agent.py`](src/agentx/agent.py#L4) branches on:

- `not goal or not str(goal).strip()`
- `any((w in low for w in WRITES))`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 13. What does the operations plane add, and where is its limit?

[`src/agentx/ops.py`](src/agentx/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
