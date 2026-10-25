"""Append-only simulation assessment authoring, never a physical health review."""
import json
from typing import Literal

from fastapi import Depends
from pydantic import Field

from .imports import Problem, dump, now
from .recovery import Body, audit, fingerprint, identifier, remember, replay


class AssessmentBody(Body):
    health: Literal["healthy", "faulty", "unknown"]
    expected_revision: int = Field(ge=0, strict=True)
    expected_assessment_id: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=200)
    evidence_ref: str = Field(min_length=11, max_length=2000, pattern=r"^synthetic:.+")
    notes: str = Field(default="", max_length=2000)
    simulation_only: Literal[True]


def subject(c, kind, subject_id):
    if kind not in ("computer", "component"):
        raise Problem(422, "SUBJECT_TYPE_INVALID", "Select computer or component.")
    table = "computers" if kind == "computer" else "components"
    row = c.execute(f"SELECT * FROM {table} WHERE id=?", (subject_id,)).fetchone()
    if not row:
        raise Problem(404, "SUBJECT_NOT_FOUND", "Select an imported subject.")
    return table, row


def install_routes(app, headers):
    db = app.state.db

    @app.get("/api/v1/assessments/{kind}/{subject_id}")
    def history(kind: str, subject_id: str):
        with db.connect() as c:
            _, row = subject(c, kind, subject_id)
            return {"current_assessment_id": row["assessment_id"], "items": [
                {"id": a["id"], **json.loads(a["data"])} for a in c.execute(
                    "SELECT * FROM assessments WHERE subject_type=? AND subject_id=? ORDER BY rowid",
                    (kind, subject_id))]}

    @app.post("/api/v1/assessments/{kind}/{subject_id}")
    def author(kind: str, subject_id: str, body: AssessmentBody, identity=Depends(headers)):
        actor, key = identity
        fp = fingerprint(f"assessment:{kind}:{subject_id}", body.model_dump(), actor)
        if not body.source.strip() or not body.evidence_ref.removeprefix("synthetic:").strip():
            raise Problem(422, "ASSESSMENT_INVALID", "Supply an authored source and synthetic evidence reference.")
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            prior = replay(c, key, fp)
            if prior:
                return prior
            table, row = subject(c, kind, subject_id)
            fleet = c.execute("SELECT * FROM fleets WHERE id=?", (row["fleet_id"],)).fetchone()
            if fleet["mode"] != "simulation":
                raise Problem(422, "PHYSICAL_REVIEW_UNAVAILABLE", "This action authors synthetic assertions only.")
            if fleet["revision"] != body.expected_revision:
                raise Problem(409, "INVENTORY_CHANGED", "Refresh inventory and review its current revision before authoring.")
            if row["assessment_id"] != body.expected_assessment_id:
                raise Problem(409, "ASSESSMENT_CHANGED", "Refresh the subject's assessment history before authoring.")
            # Evidence cannot silently invalidate an executing or approved fleet.
            if c.execute("SELECT 1 FROM recovery_plans WHERE fleet_id=? AND status='approved' LIMIT 1", (row["fleet_id"],)).fetchone() or c.execute(
                "SELECT 1 FROM recovery_steps s JOIN recovery_orders o ON o.id=s.order_id JOIN recovery_plans p ON p.id=o.plan_id WHERE p.fleet_id=? AND (s.status='done' OR s.status IN ('fail','inconclusive')) LIMIT 1", (row["fleet_id"],)).fetchone():
                raise Problem(409, "EXECUTION_EVIDENCE_LOCKED", "This fleet has approved or recorded work. Preserve that evidence; author assessments before approval in a separate imported fleet.")
            original = json.loads(c.execute("SELECT data FROM assessments WHERE id=?", (row["assessment_id"],)).fetchone()["data"])
            if original["assessment_kind"] != "authored_synthetic_assertion":
                raise Problem(422, "SYNTHETIC_SUBJECT_REQUIRED", "Only an existing synthetic subject can receive this authored assertion.")
            assessment_id, timestamp = identifier("assessment"), now()
            assessment = {**original, "health": body.health, "assessment_kind": "authored_synthetic_assertion",
                "source": body.source.strip(), "provenance": "synthetic:manual-authoring",
                "evidence_ref": body.evidence_ref.strip(), "recorded_value": timestamp, "recorded_precision": "datetime",
                "supplied_author_label": actor, "human_reviewed": False, "human_reviewer": None,
                "acceptance_scope": "simulation-only", "context_source": "explicit local synthetic authoring; not physical evidence",
                "parent_assessment_id": row["assessment_id"], "authored_at": timestamp, "authored_by": actor,
                "notes": body.notes.strip(), "contract_version": "simulation-assessment-v1"}
            c.execute("INSERT INTO assessments VALUES (?,?,?,?,?)", (assessment_id, kind, subject_id, row["batch_id"], dump(assessment)))
            # Original imported row JSON and prior assessment rows remain intact.
            c.execute(f"UPDATE {table} SET assessment_id=? WHERE id=?", (assessment_id, subject_id))
            c.execute("UPDATE fleets SET revision=revision+1 WHERE id=?", (row["fleet_id"],))
            c.execute("UPDATE recovery_plans SET status='stale' WHERE fleet_id=? AND status='validated'", (row["fleet_id"],))
            result = {"id": assessment_id, "subject_type": kind, "subject_id": subject_id,
                      "revision": fleet["revision"] + 1, "assessment": assessment, "mode": "simulation"}
            audit(c, "synthetic_assessment_authored", subject_id, actor, result)
            remember(c, key, fp, result)
            c.commit()
            return result
