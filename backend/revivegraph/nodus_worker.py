"""CPU job entry point. No database, API credential or handwritten plan required."""
import json
import sys
from pathlib import Path

from .execution_protocol import PROTOCOL, canonical, digest, request
from .optimizer import solve


def run(input_path, output_path):
    raw = Path(input_path).read_bytes()
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Input exceeds the 4 MiB job limit.")
    payload = json.loads(raw)
    source = json.loads(Path("source-manifest.json").read_text(encoding="utf-8"))
    for name, expected in source.items():
        import hashlib
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError("Uploaded source does not match manifest.")
    expected = request(payload["snapshot"], payload["budget_paise"], payload["time_minutes"], digest(source))
    if expected != payload:
        raise ValueError("Input contract or source identity mismatch.")
    result = solve(payload["snapshot"], payload["budget_paise"], payload["time_minutes"])
    output = {"protocol": PROTOCOL, "input_hash": digest(payload), "source_hash": payload["source_hash"],
              "output_hash": digest(result), "result": result}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(canonical(output), encoding="utf-8")
    print(canonical({"event": "cpu_calculation_complete", "input_hash": output["input_hash"],
                     "output_hash": output["output_hash"], "status": result["solver"]["status"]}), flush=True)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
