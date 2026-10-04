TOOLS = ["profile_table", "run_sql", "stats", "chart"]
WRITES = ("delete", "drop", "update", "insert",)

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
