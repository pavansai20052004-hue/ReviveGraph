"""Read optional project-local secrets without exposing them through public APIs."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {"AGENT37_API_KEY", "AGENT37_INSTANCE_URL", "AGENT37_PROFILE", "REVIVEGRAPH_AGENT37_ENABLED",
           "REVIVEGRAPH_AGENT37_INSTANCE_REVIEWED",
           "RENDER_API_KEY", "RENDER_WORKFLOW_SLUG", "REVIVEGRAPH_RENDER_TASK", "REVIVEGRAPH_RENDER_ENABLED"}


def settings():
    values = {}
    path = ROOT / ".env.onsite"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() in ALLOWED:
                values[name.strip()] = value.strip().strip('"').strip("'")
    values.update({name: os.environ[name] for name in ALLOWED if name in os.environ})
    return values
