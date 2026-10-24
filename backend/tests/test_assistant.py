"""Preparation uses test-authored actors and transport doubles, never live AI credit."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from test_recovery import env, plan, post
from revivegraph import assistant
from revivegraph.main import create_app


def configured(monkeypatch):
    monkeypatch.setenv('AGENT37_INSTANCE_URL', 'https://test-instance.agent37.app')
    monkeypatch.setenv('AGENT37_API_KEY', 'test-key-not-a-real-secret')
    monkeypatch.setenv('REVIVEGRAPH_AGENT37_ENABLED', '1')
    monkeypatch.setenv('REVIVEGRAPH_AGENT37_INSTANCE_REVIEWED', '1')


def test_local_facts_replay_evidence_and_restart(env, monkeypatch):
    app, client, path = env
    p = plan(client)
    before = client.get('/api/v1/components').json()
    monkeypatch.setattr(assistant, 'agent37_select', lambda *a, **k: pytest.fail('Local summary must not call a provider'))
    facts = client.get(f"/api/v1/plans/{p['id']}/assistant-context?asset_id=RG-PC-06")
    assert facts.status_code == 200, facts.text
    facts = facts.json()
    mismatch = next(f for f in facts['facts'] if f['id'] == 'inspection:RG-PC-06:RG-RAM-11')
    assert mismatch['data']['hardware']['decision'] == 'incompatible'
    assert 'RAM_GENERATION' in mismatch['text']
    unknown = [f for f in facts['facts'] if f['id'].startswith('inspection:') and 'HEALTH_UNKNOWN' in f['text']]
    assert unknown and all(f['data']['eligibility']['eligible'] is False for f in unknown)
    assert any(f['id'].startswith('alternative:') for f in facts['facts'])
    body = {'question': 'Explain the plan', 'provider': 'facts'}
    r = post(client, f"/plans/{p['id']}/assistant", body, 'summary')
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['physical_repairs'] == 0 and result['provider'] == 'facts'
    assert result['input_hash'] == p['input_hash']
    assert post(client, f"/plans/{p['id']}/assistant", body, 'summary').json() == result
    assert post(client, f"/plans/{p['id']}/assistant", {**body, 'question': 'different'}, 'summary').status_code == 409
    with app.state.db.connect() as c:
        events = c.execute("SELECT * FROM audit_events WHERE action='assistant_explanation'").fetchall()
        assert len(events) == 1 and events[0]['actor'] == 'test-human'
    reopened = TestClient(create_app(path))
    assert post(reopened, f"/plans/{p['id']}/assistant", body, 'summary').json() == result
    assert reopened.get('/api/v1/components').json() == before


@pytest.mark.parametrize('value', ['http://localhost', 'https://evil.example', 'https://a.agent37.app:wrong', 'https://a.agent37.app/path', 'https://user:pass@a.agent37.app', 'https://[bad'])
def test_provider_url_restricted(monkeypatch, value):
    monkeypatch.setenv('AGENT37_INSTANCE_URL', value)
    assert assistant.configuration()[2] is False


@pytest.mark.parametrize('data', [
    {'status': 'failed', 'output_text': '{"fact_ids":["plan-summary"]}'},
    {'status': 'completed', 'output_text': '{"fact_ids":["invented-repair"]}'},
    {'status': 'completed', 'output_text': '{"fact_ids":["plan-summary"],"claim":"100 repaired"}'},
    {'status': 'completed', 'output_text': '{"fact_ids":[true]}'},
    {'status': 'completed', 'output_text': 'Seven physical repairs completed'},
    ['unexpected-array'],
    {'status': 'completed', 'output_text': 123},
])
def test_unsupported_model_output_rejected(monkeypatch, data):
    configured(monkeypatch)
    monkeypatch.setattr(httpx.Client, 'post', lambda *a, **k: httpx.Response(200, json=data, request=httpx.Request('POST', 'https://test-instance.agent37.app/v1/responses')))
    cfg, url, _ = assistant.configuration()
    with pytest.raises(assistant.Problem) as error:
        assistant.agent37_select('question', {'plan_id':'test','input_hash':'hash','facts':[{'id':'plan-summary'}]}, cfg, url)
    assert error.value.code == 'AGENT37_RESPONSE_REJECTED'


def test_agent37_transport_selection_no_paid_retry(env, monkeypatch):
    app, client, _ = env
    p = plan(client)
    configured(monkeypatch)
    calls = []
    original_post = httpx.Client.post
    def remote(self, url, **kwargs):
        if isinstance(self, TestClient):
            return original_post(self, url, **kwargs)
        calls.append((url, kwargs))
        return httpx.Response(200, json={'id':'mock-response-not-live', 'status':'completed', 'output_text':json.dumps({'fact_ids':['plan-summary','greedy-comparison']}), 'usage':{'cost_usd':None}}, request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx.Client, 'post', remote)
    r = post(client, f"/plans/{p['id']}/assistant", {'question':'Why this allocation?','provider':'agent37'}, 'ai-selection')
    assert r.status_code == 200, r.text
    assert r.json()['provider_evidence']['response_id'] == 'mock-response-not-live'
    assert [f['id'] for f in r.json()['facts']] == ['plan-summary','greedy-comparison']
    assert calls[0][0].endswith('/v1/responses')
    assert calls[0][1]['headers']['X-Agent37-Key'] == 'test-key-not-a-real-secret'
    assert post(client, f"/plans/{p['id']}/assistant", {'question':'Why this allocation?','provider':'agent37'}, 'ai-selection').json() == r.json()
    assert len(calls) == 1
    def timeout(self, url, **kwargs):
        if isinstance(self, TestClient):
            return original_post(self, url, **kwargs)
        raise httpx.ReadTimeout('test timeout')
    monkeypatch.setattr(httpx.Client, 'post', timeout)
    body = {'question':'timeout','provider':'agent37'}
    assert post(client, f"/plans/{p['id']}/assistant", body, 'timeout').status_code == 502
    assert post(client, f"/plans/{p['id']}/assistant", body, 'timeout').status_code == 409
    with app.state.db.connect() as c:
        assert c.execute('SELECT COUNT(*) FROM recovery_decisions').fetchone()[0] == 0


@pytest.mark.parametrize('gate', ['REVIVEGRAPH_AGENT37_ENABLED', 'REVIVEGRAPH_AGENT37_INSTANCE_REVIEWED'])
def test_unconfigured_agent_does_not_create_attempt(env, monkeypatch, gate):
    app, client, _ = env
    p = plan(client)
    configured(monkeypatch)
    monkeypatch.setenv(gate, '0')
    r = post(client, f"/plans/{p['id']}/assistant", {'question':'test','provider':'agent37'}, 'unconfigured')
    assert r.status_code == 503
    with app.state.db.connect() as c:
        assert c.execute('SELECT * FROM recovery_requests WHERE key=?', ('unconfigured',)).fetchone() is None


def test_failed_donor_facts_are_excluded_and_original_is_stale(env):
    _, client, _ = env
    p = plan(client)
    parts = {x['component_id']: x for x in client.get('/api/v1/components').json()['items']}
    target, donor = next((a['target_asset_id'], x) for a in p['result']['allocations'] for x in a['ram_component_ids']+[a['storage_component_id']] if parts[x]['location_asset_id'] and parts[x]['location_asset_id'] != a['target_asset_id'])
    revised = post(client, f"/plans/{p['id']}/failures", {'component_id':donor}).json()
    r = client.get(f"/api/v1/plans/{revised['id']}/assistant-context?asset_id={target}")
    assert r.status_code == 200, r.text
    evidence = r.json()
    fact = next(f for f in evidence['facts'] if f['id'] == f'inspection:{target}:{donor}')
    assert fact['data']['eligibility']['eligible'] is False
    assert fact['data']['eligibility']['availability'] == 'scenario_excluded'
    assert any(f['id'] == 'failure-comparison' for f in evidence['facts'])
    original = client.get(f"/api/v1/plans/{p['id']}/assistant-context").json()
    assert original['plan_status'] == 'stale'
    assert any(f['id'] == 'plan-action-blocked' for f in original['facts'])


def test_status_changed_during_provider_call_is_not_accepted(env, monkeypatch):
    app, client, _ = env
    p = plan(client)
    configured(monkeypatch)
    def mutate(*args):
        with app.state.db.connect() as c:
            c.execute("UPDATE recovery_plans SET status='stale' WHERE id=?", (p['id'],))
            c.commit()
        return ['plan-summary'], {'status':'mock-only'}
    monkeypatch.setattr(assistant, 'agent37_select', mutate)
    r = post(client, f"/plans/{p['id']}/assistant", {'question':'explain','provider':'agent37'})
    assert r.status_code == 409 and r.json()['error']['code'] == 'PLAN_STATUS_CHANGED'
    with app.state.db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM audit_events WHERE action='assistant_explanation'").fetchone()[0] == 0
