"""Preparation-free onsite adapter tests: fake transport is never remote evidence."""
import copy
import json
from types import SimpleNamespace

import pytest

from test_optimizer import snapshot
from test_recovery import env, post, plan
from revivegraph.execution import execute, prepare, sanitize
from revivegraph.execution_protocol import PROTOCOL, accept, canonical, digest
from revivegraph.imports import Problem
from revivegraph.nodus_worker import run
from revivegraph.optimizer import solve


@pytest.fixture
def payload_output(tmp_path, snapshot):
    source = tmp_path / "upload"
    source.mkdir()
    payload = prepare(source, snapshot, 250000, 330)
    result = solve(snapshot, 250000, 330)
    output = {"protocol": PROTOCOL, "input_hash": digest(payload), "source_hash": payload["source_hash"],
              "output_hash": digest(result), "result": result}
    return payload, output, source


def test_roundtrip_allowlisted_worker(payload_output, monkeypatch, tmp_path):
    payload, output, source = payload_output
    assert {str(p.relative_to(source)).replace('\\', '/') for p in source.rglob('*') if p.is_file()} == {
        'revivegraph/__init__.py', 'revivegraph/domain.py', 'revivegraph/optimizer.py',
        'revivegraph/execution_protocol.py', 'revivegraph/nodus_worker.py',
        'requirements.txt', 'source-manifest.json', 'input.json'}
    monkeypatch.chdir(source)
    destination = tmp_path / 'worker-result.json'
    run(source / 'input.json', destination)
    result = accept(payload, json.loads(destination.read_text()))
    assert result['totals'] == output['result']['totals']


@pytest.mark.parametrize('mutation', ['input', 'source', 'output', 'protocol', 'double_use',
                                     'totals', 'numeric_type', 'operations', 'baseline', 'status', 'version'])
def test_untrusted_output_rejected(payload_output, mutation):
    payload, original, _ = payload_output
    value = copy.deepcopy(original)
    if mutation in ('input', 'source', 'output'):
        value[mutation + '_hash'] = 'wrong'
    elif mutation == 'protocol':
        value['protocol'] = 'future'
    elif mutation == 'double_use':
        value['result']['allocations'][1]['storage_component_id'] = value['result']['allocations'][0]['storage_component_id']
    elif mutation == 'totals':
        value['result']['totals']['cost_paise'] = 0
    elif mutation == 'numeric_type':
        value['result']['totals']['cost_paise'] = float(value['result']['totals']['cost_paise'])
    elif mutation == 'operations':
        value['result']['operations'] = []
    elif mutation == 'baseline':
        value['result']['baseline']['totals']['usable_final'] = 99
    elif mutation == 'status':
        value['result']['solver']['status'] = 'UNKNOWN'
    elif mutation == 'version':
        value['result']['solver']['ortools_version'] = 'unknown'
    if mutation not in ('input', 'source', 'output', 'protocol'):
        value['output_hash'] = digest(value['result'])  # Hash alone is insufficient.
    with pytest.raises(ValueError):
        accept(payload, value)


def fake_sdk(output, failing=False):
    calls = []
    class Job:
        name = 'fake-test-job-never-a-remote-run'
        @classmethod
        def run(cls, **kwargs):
            calls.append(kwargs)
            if callable(output):
                cls.download_output = output(json.loads((kwargs['source'] / 'input.json').read_text(encoding='utf-8')))
            else:
                cls.download_output = output
            return cls()
        def wait(self, timeout):
            if failing:
                raise TimeoutError()
        def status(self):
            return {'phase': 'Succeeded', 'unitMetrics': {'cpuSeconds': 2}, 'cost': {'actualUSD': '0.001'}}
        def logs(self, **kwargs):
            return ['test-only log\n']
        def cancel(self):
            calls.append('cancel')
        @property
        def outputs(self):
            def download(path):
                path.write_text(canonical(self.download_output), encoding='utf-8')
            return {'result': SimpleNamespace(download=download)}
    return SimpleNamespace(Job=Job), calls


def test_remote_transport_cap_receipt_and_duplicate_guard(payload_output, snapshot, monkeypatch, tmp_path):
    _, output, _ = payload_output
    sdk, calls = fake_sdk(output)
    monkeypatch.setenv('REVIVEGRAPH_NODUS_ENABLED', '1')
    result, receipt = execute(snapshot, 250000, 330, 'nodus', sdk=sdk, evidence_root=tmp_path/'runs', run_key='one')
    assert result['totals'] == output['result']['totals']
    assert receipt['accepted'] and receipt['provider'] == 'nodus'
    assert calls[0]['cpu'] == 1 and calls[0]['max_cost'] == 0.10 and calls[0]['timeout'] == '5m'
    assert receipt['usage'] == {'cpuSeconds': 2}
    with pytest.raises(Problem) as exc:
        execute(snapshot, 250000, 330, 'nodus', sdk=sdk, evidence_root=tmp_path/'runs', run_key='one')
    assert exc.value.code == 'NODUS_ATTEMPT_EXISTS' and len(calls) == 1


def test_timeout_cancel_no_local_fallback(payload_output, snapshot, monkeypatch, tmp_path):
    _, output, _ = payload_output
    sdk, calls = fake_sdk(output, failing=True)
    monkeypatch.setenv('REVIVEGRAPH_NODUS_ENABLED', '1')
    with pytest.raises(Problem) as exc:
        execute(snapshot, 250000, 330, 'nodus', sdk=sdk, evidence_root=tmp_path/'runs')
    assert exc.value.code == 'NODUS_CALCULATION_FAILED' and calls[-1] == 'cancel'
    receipt = json.loads(next((tmp_path/'runs').rglob('receipt.json')).read_text())
    assert not receipt['accepted'] and receipt['job_id'].startswith('fake-test')
    assert receipt['usage'] == {'cpuSeconds': 2}
    assert next((tmp_path/'runs').rglob('logs.txt')).read_text() == 'test-only log\n'


def test_disabled_remote_no_plan_write_and_local_still_works(env, monkeypatch):
    app, client, _ = env
    monkeypatch.delenv('REVIVEGRAPH_NODUS_ENABLED', raising=False)
    response = post(client, '/plans', {'execution': 'nodus'})
    assert response.status_code == 503
    assert client.get('/api/v1/plans').json()['items'] == []
    local = plan(client)
    assert local['execution']['provider'] == 'local'
    assert post(client, '/plans', {'execution': 'unknown'}).status_code == 422


def test_sanitization(monkeypatch):
    monkeypatch.setenv('NODUS_API_KEY', 'known-environment-key')
    text = sanitize('Bearer abc123 token=secret {"api_key":"json-secret"} known-environment-key https://storage.example/result?signature=private')
    assert 'abc123' not in text and 'secret' not in text and 'signature' not in text
    assert 'known-environment-key' not in text


def test_remote_api_persistence_audit_and_provider_inheritance(env, monkeypatch, tmp_path):
    import revivegraph.execution as execution
    from revivegraph.main import create_app
    from fastapi.testclient import TestClient
    _, client, db_path = env
    def output(payload):
        result = solve(payload['snapshot'], payload['budget_paise'], payload['time_minutes'])
        return {'protocol': PROTOCOL, 'input_hash': digest(payload), 'source_hash': payload['source_hash'],
                'output_hash': digest(result), 'result': result}
    sdk, calls = fake_sdk(output)
    monkeypatch.setenv('REVIVEGRAPH_NODUS_ENABLED', '1')
    original = execution.execute
    def isolated(*args, **kwargs):
        return original(*args, **kwargs, sdk=sdk, evidence_root=tmp_path/'remote-evidence')
    monkeypatch.setattr(execution, 'execute', isolated)
    p = plan(client, execution='nodus')
    assert p['execution']['provider'] == 'nodus'
    report = client.get(f"/api/v1/plans/{p['id']}/report").json()
    assert 'fake-test-job-never-a-remote-run' in canonical(report)
    restored = TestClient(create_app(db_path)).get(f"/api/v1/plans/{p['id']}").json()
    assert restored['execution'] == p['execution']
    donor = next(o for o in p['result']['operations'] if o.get('target_asset_id') and o['asset_id'] != o['target_asset_id'])
    revised = post(client, f"/plans/{p['id']}/failures", {'component_id': donor['component_id']})
    assert revised.status_code == 200, revised.text
    assert revised.json()['execution']['provider'] == 'nodus' and len(calls) == 2
    assert client.get('/api/v1/state').json()['recovery']['physical_passes'] == 0
