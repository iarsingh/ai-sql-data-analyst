from agentx.progression import sql_agent

def test_sql_agent_explains_drop():
    tables = {"revenue": [{"month": "2026-08", "amount": 100}, {"month": "2026-09", "amount": 40}]}
    out = sql_agent("Why did revenue fall last month?", tables)
    assert "postgres" in out["tools"]
    assert out["applied"] is False
    assert "lower" in out["explanation"].lower()

