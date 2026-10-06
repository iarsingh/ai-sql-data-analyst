# ai-sql-data-analyst — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

Question → agent chooses profile/SQL/stats/viz tools → explanation. Writes refused.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/agentx/agent.py"]
    M1["src/agentx/main.py"]
    M2["src/agentx/ops.py"]
    M1 -->|imports| M0
    M1 -->|imports| M2
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/agentx/main.py`](src/agentx/main.py) | HTTP handlers: `GET /healthz`, `POST /agent/run` |
| [`src/agentx/ops.py`](src/agentx/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/agentx/agent.py`](src/agentx/agent.py) | Functions: `run` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_agent.py`](tests/test_agent.py) | Executable checks and regression examples |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

## Existing design and operating guides

These checked-in guides provide the project’s detailed design, operational context, or deployment view:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/agentx/main.py`](src/agentx/main.py#L8) |
| `POST /agent/run` | `post_run` | [`src/agentx/main.py`](src/agentx/main.py#L12) |
| `GET /readyz` | `readyz` | [`src/agentx/ops.py`](src/agentx/ops.py#L74) |
| `POST /workspaces` | `create_workspace` | [`src/agentx/ops.py`](src/agentx/ops.py#L80) |
| `GET /workspaces` | `list_workspaces` | [`src/agentx/ops.py`](src/agentx/ops.py#L98) |
| `POST /workspaces/{workspace_id}/jobs` | `create_job` | [`src/agentx/ops.py`](src/agentx/ops.py#L106) |
| `GET /jobs/{job_id}` | `get_job` | [`src/agentx/ops.py`](src/agentx/ops.py#L130) |
| `POST /jobs/{job_id}/approve` | `approve_job` | [`src/agentx/ops.py`](src/agentx/ops.py#L140) |
| `GET /audit` | `audit` | [`src/agentx/ops.py`](src/agentx/ops.py#L160) |
| `GET /metrics` | `metrics` | [`src/agentx/ops.py`](src/agentx/ops.py#L176) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `run(goal, payload)`

Source: [`src/agentx/agent.py`](src/agentx/agent.py#L4).

Calls visible in this function: `ValueError`, `any`, `float`, `goal.lower`, `list`, `payload.get`, `row.get`, `str`, `str(goal).strip`, `totals.get`.

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

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `ValueError('goal is empty')` | [`src/agentx/agent.py`](src/agentx/agent.py#L6) |
| `HTTPException(422, str(exc))` | [`src/agentx/main.py`](src/agentx/main.py#L16) |
| `HTTPException(status_code=404, detail='workspace not found')` | [`src/agentx/ops.py`](src/agentx/ops.py#L77) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/agentx/ops.py`](src/agentx/ops.py#L100) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/agentx/ops.py`](src/agentx/ops.py#L109) |
| `HTTPException(status_code=403, detail='production apply is disabled in this lab')` | [`src/agentx/ops.py`](src/agentx/ops.py#L113) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/agentx/agent.py`](src/agentx/agent.py) defines module-level containers: `TOOLS`.
- [`src/agentx/ops.py`](src/agentx/ops.py) defines module-level containers: `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `run`

In [`src/agentx/agent.py`](src/agentx/agent.py#L4), `run(goal, payload)` receives the inputs. The function computes these intermediate values:

- `low = goal.lower()`
- `rows = payload.get('rows') or []`
- `totals = {}`
- `result = {'by_region': totals, 'chart': list(totals)}`

Its result is defined by:

- `{'refused': False, 'tools': TOOLS, 'analysis': result, 'applied': False, 'needs_approval': False}`
- `{'refused': True, 'reason': 'destructive action requires a human', 'applied': False, 'tools': []}`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/agentx/agent.py`](src/agentx/agent.py#L4) branches on:

- `not goal or not str(goal).strip()`
- `any((w in low for w in WRITES))`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

### What does the operations plane add, and where is its limit

[`src/agentx/ops.py`](src/agentx/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_agent.py`](tests/test_agent.py), [`tests/test_ops.py`](tests/test_ops.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
