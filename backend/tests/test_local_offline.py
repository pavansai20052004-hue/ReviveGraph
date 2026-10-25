"""Process-scoped network denial for the real local deterministic pipeline."""
import socket
import ipaddress

from test_recovery import env, plan, post


def test_local_pipeline_and_evidence_need_no_external_network(env, monkeypatch):
    _, client, _ = env
    attempts = []
    def local(host):
        if host == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False
    getaddrinfo, connect, connect_ex = socket.getaddrinfo, socket.socket.connect, socket.socket.connect_ex
    def dns(host, *args, **kwargs):
        if not local(host):
            attempts.append(str(host)); raise AssertionError("External DNS denied")
        return getaddrinfo(host, *args, **kwargs)
    def guarded(original):
        def call(sock, address, *args, **kwargs):
            if not isinstance(address, tuple) or not local(address[0]):
                attempts.append(str(address)); raise AssertionError("External connection denied")
            return original(sock, address, *args, **kwargs)
        return call
    # Windows asyncio uses a loopback socket pair for its own event loop.
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket.socket, "connect", guarded(connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guarded(connect_ex))
    p = plan(client, context="network-denied-local")
    assert p["execution"]["provider"] == "local"
    summary = post(client, f"/plans/{p['id']}/assistant", {"provider": "facts", "question": "Read validated plan evidence"})
    assert summary.status_code == 200, summary.text
    assert summary.json()["physical_repairs"] == 0
    assert attempts == []
