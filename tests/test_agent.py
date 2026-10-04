from fastapi.testclient import TestClient
from agentx.main import app
client = TestClient(app)

def test_run_and_refuse():
    payload = client.post("/agent/run", json={"goal": 'Why did revenue fall last month?', "payload": {'rows': [{'region': 'north', 'revenue': 10}, {'region': 'south', 'revenue': 30}]}}).json()
    assert payload["refused"] is False
    assert payload["applied"] is False
    assert payload["analysis"]["by_region"]["south"] == 30
    refused = client.post("/agent/run", json={"goal": 'delete old revenue rows'}).json()
    assert refused["refused"] is True
