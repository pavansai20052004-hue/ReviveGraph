"""Local evidence and removed-provider regression tests; no live service calls."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from test_recovery import env, plan, post
from revivegraph import assistant
from revivegraph.main import create_app


def test_local_facts_replay_evidence_and_restart(env, monkeypatch):
    app, client, path = env
    p = plan(client)
    before = client.get('/api/v1/components').json()
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', lambda *a, **k: pytest.fail('Local summary must not make a network request'))
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



@pytest.mark.parametrize('provider', ['agent37', 'another-external-provider'])
def test_removed_provider_rejected_before_any_attempt(env, monkeypatch, provider):
    app, client, _ = env
    p = plan(client)
    # Even stale locally stored configuration cannot reactivate the removed code.
    monkeypatch.setenv('AGENT37_INSTANCE_URL', 'https://test-instance.agent37.app')
    monkeypatch.setenv('AGENT37_API_KEY', 'mock-key-not-a-real-secret')
    monkeypatch.setenv('REVIVEGRAPH_AGENT37_ENABLED', '1')
    monkeypatch.setenv('REVIVEGRAPH_AGENT37_INSTANCE_REVIEWED', '1')
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', lambda *a, **k: pytest.fail('Removed provider must never contact the network'))
    with app.state.db.connect() as c:
        before = c.execute('SELECT COUNT(*) FROM recovery_requests').fetchone()[0]
    r = post(client, f"/plans/{p['id']}/assistant", {'question':'explain','provider':provider}, 'removed-provider')
    assert r.status_code == 410, r.text
    assert r.json()['error']['code'] == 'EXPLANATION_PROVIDER_REMOVED'
    with app.state.db.connect() as c:
        assert c.execute('SELECT COUNT(*) FROM recovery_requests').fetchone()[0] == before
        assert c.execute("SELECT COUNT(*) FROM audit_events WHERE action='assistant_explanation'").fetchone()[0] == 0
        assert c.execute('SELECT COUNT(*) FROM recovery_decisions').fetchone()[0] == 0


def test_public_integrations_and_settings_do_not_expose_removed_provider(env, monkeypatch, tmp_path):
    from revivegraph import settings
    _, client, _ = env
    (tmp_path / '.env.onsite').write_text('AGENT37_API_KEY=mock-removed-value\nAGENT37_INSTANCE_URL=https://test.agent37.app\nRENDER_API_KEY=mock-render-value\n')
    monkeypatch.setattr(settings, 'ROOT', tmp_path)
    monkeypatch.setenv('REVIVEGRAPH_AGENT37_ENABLED', '1')
    result = settings.settings()
    assert not any('AGENT37' in name for name in result)
    assert result['RENDER_API_KEY'] == 'mock-render-value'
    integrations = client.get('/api/v1/integrations').json()
    assert 'agent37' not in integrations
    assert integrations['assistant'] == {'provider':'facts','network_requests':False}
    assert 'mock-render-value' not in json.dumps(integrations)


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



def test_status_changed_during_local_summary_is_not_accepted(env, monkeypatch):
    app, client, _ = env
    p = plan(client)
    original = assistant.select_facts
    def mutate(evidence, asset_id):
        with app.state.db.connect() as c:
            c.execute("UPDATE recovery_plans SET status='stale' WHERE id=?", (p['id'],))
            c.commit()
        return original(evidence, asset_id)
    monkeypatch.setattr(assistant, 'select_facts', mutate)
    r = post(client, f"/plans/{p['id']}/assistant", {'question':'review','provider':'facts'})
    assert r.status_code == 409 and r.json()['error']['code'] == 'PLAN_STATUS_CHANGED'
    with app.state.db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM audit_events WHERE action='assistant_explanation'").fetchone()[0] == 0


def test_invalid_stored_plan_and_unknown_asset_are_rejected(env):
    app, client, _ = env
    p = plan(client)
    r = client.get(f"/api/v1/plans/{p['id']}/assistant-context?asset_id=unknown-asset")
    assert r.status_code == 404
    with app.state.db.connect() as c:
        data = json.loads(c.execute("SELECT data FROM recovery_plans WHERE id=?", (p['id'],)).fetchone()['data'])
        data['output_hash'] = 'tampered'
        c.execute("UPDATE recovery_plans SET data=? WHERE id=?", (json.dumps(data), p['id']))
        c.commit()
    r = post(client, f"/plans/{p['id']}/assistant", {'question':'review'})
    assert r.status_code == 409 and r.json()['error']['code'] == 'PLAN_INVALID'


def test_historical_external_explanation_audit_is_preserved(env):
    app, client, _ = env
    p = plan(client)
    historical = {'provider':'agent37','label':'Historical mock provider record','asset_id':None,'facts':[]}
    with app.state.db.connect() as c:
        assistant.audit(c, 'assistant_explanation', p['id'], 'test-historical-actor', historical)
        c.commit()
    post(client, f"/plans/{p['id']}/assistant", {'question':'new local summary','provider':'facts'})
    events = client.get(f"/api/v1/plans/{p['id']}/report").json()['audit_events']
    assert any(e['action']=='assistant_explanation' and e['data']==historical for e in events)
    assert any(e['action']=='assistant_explanation' and e['data'].get('provider')=='facts' for e in events)
