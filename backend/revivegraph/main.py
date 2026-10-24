import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, File, Form, Header, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .db import Database
from .domain import RULE_VERSION, eligibility, part_compatibility, ram_configuration, reason, usability
from .imports import (MAX_FILE_BYTES, Problem, assessment_for, dump, get_registration, now,
                      register_fixture, registration_public, sha, validate_csv_pair)

ROOT = Path(__file__).resolve().parents[2]
Mode = Literal["simulation", "physical"]


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegistrationBody(StrictBody):
    fixture_id: str = "revivegraph-synthetic-v1"


class CommitBody(StrictBody):
    preview_hash: str
    expected_revision: int = Field(ge=0)


class ConfigurationBody(StrictBody):
    target_asset_id: str
    ram_component_ids: list[str]
    storage_component_id: str
    mode: Mode = "simulation"


def mutation_headers(x_actor_id: Annotated[str, Header(min_length=1, max_length=100)],
                     idempotency_key: Annotated[str, Header(min_length=1, max_length=200)]):
    if not x_actor_id.strip() or not idempotency_key.strip():
        raise Problem(422, "IDENTITY_REQUIRED", "Supply a non-empty local actor and idempotency key.")
    return x_actor_id.strip(), idempotency_key


def batch_public(row):
    report = json.loads(row["report"])
    payload = json.loads(row["payload"])
    return {"batch_id": row["id"], "preview_hash": row["id"], "registration_id": row["registration_id"],
            "fleet_id": row["fleet_id"], "mode": row["mode"], "expected_revision": row["preview_revision"],
            "file_hashes": payload["file_hashes"], "valid": report["valid"], "errors": report["errors"],
            "inspection_rule_version": payload["inspection_rule_version"],
            "counts": report["counts"], "preview": {"computers": report["computers"], "components": report["components"]},
            "committed": row["committed_revision"] is not None, "revision": row["committed_revision"],
            "created_at": row["created_at"], "committed_at": row["committed_at"]}


def inventory(connection, fleet_id):
    computers, components = [], []
    registrations = {r["id"]: json.loads(r["data"]) for r in connection.execute("SELECT * FROM registrations")}
    assessments = {r["id"]: json.loads(r["data"]) for r in connection.execute("SELECT * FROM assessments")}
    for row in connection.execute("SELECT * FROM components WHERE fleet_id=? ORDER BY id", (fleet_id,)):
        if registrations[row["registration_id"]].get("inspection_rule_version") != RULE_VERSION:
            raise Problem(409, "RULE_VERSION_MISMATCH", "Inventory is pinned to another inspection rule version. Start the matching backend before inspecting it.")
        components.append({**json.loads(row["data"]), "location_asset_id": row["location_asset_id"],
                           "origin_asset_id": row["origin_asset_id"], "origin_location_kind": "installed" if row["origin_asset_id"] else "stock",
                           "registration_id": row["registration_id"], "batch_id": row["batch_id"],
                           "assessment": assessments[row["assessment_id"]], "reserved": False,
                           "inspection_rule_version": registrations[row["registration_id"]]["inspection_rule_version"]})
    for row in connection.execute("SELECT * FROM computers WHERE fleet_id=? ORDER BY id", (fleet_id,)):
        computer = {**json.loads(row["data"]), "assessment": assessments[row["assessment_id"]]}
        registration = registrations[row["registration_id"]]
        if registration.get("inspection_rule_version") != RULE_VERSION:
            raise Problem(409, "RULE_VERSION_MISMATCH", "Inventory is pinned to another inspection rule version.")
        profile = next(p for p in registration["board_profiles"]["profiles"] if p["id"] == row["profile_id"])
        installed = [part for part in components if part["location_asset_id"] == row["id"]]
        computers.append({**computer, "profile": profile, "registration_id": row["registration_id"] ,
                          "registration_hash": registration["registration_hash"], "batch_id": row["batch_id"],
                          "inspection_rule_version": registration["inspection_rule_version"],
                          "assessment": assessments[row["assessment_id"]], "installed_components": installed,
                          "usability": usability(computer, installed, profile)})
    return computers, components


def create_app(db_path=None, fixture_root=None):
    app = FastAPI(title="ReviveGraph recovery", version="0.2.0")
    app.state.db = Database(db_path or os.environ.get("REVIVEGRAPH_DB", str(ROOT / "data" / "revivegraph.sqlite3")))
    app.state.fixture_root = Path(fixture_root or ROOT / "datasets" / "synthetic-v1")

    @app.exception_handler(Problem)
    async def problem_handler(request: Request, exc: Problem):
        return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message,
                            "field_errors": exc.errors, "current_revision": exc.revision}, "request_id": str(uuid.uuid4())})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {"code": "REQUEST_INVALID", "message": "Check required fields and headers.",
                            "field_errors": [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()]}, "request_id": str(uuid.uuid4())})

    @app.exception_handler(sqlite3.OperationalError)
    async def database_handler(request: Request, exc: sqlite3.OperationalError):
        return JSONResponse(status_code=409, content={"error": {"code": "DATABASE_BUSY", "message": "Database operation could not complete. Retry the same request; do not edit the preview."}, "request_id": str(uuid.uuid4())})

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "schema_version": 2, "rule_version": RULE_VERSION}

    @app.get("/api/v1/fixture-registrations")
    def registrations():
        with app.state.db.connect() as connection:
            return {"items": [registration_public(r) for r in connection.execute("SELECT * FROM registrations ORDER BY created_at")]}

    @app.post("/api/v1/fixture-registrations")
    def register(body: RegistrationBody, headers=Depends(mutation_headers)):
        return register_fixture(app.state.db, app.state.fixture_root, body.fixture_id, headers[0])

    @app.get("/api/v1/bundled-fixture/{filename}")
    def bundled_csv(filename: str):
        if filename not in ("computers.csv", "components.csv"):
            raise Problem(404, "FILE_NOT_FOUND", "Only the two disclosed CSV import files are downloadable.")
        return FileResponse(app.state.fixture_root / filename, media_type="text/csv", filename=filename)

    @app.post("/api/v1/imports/preview")
    async def preview(registration_id: Annotated[str, Form()],
                      computers_file: Annotated[UploadFile, File()], components_file: Annotated[UploadFile, File()],
                      fleet_id: Annotated[str, Form(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")] = "RG-DEMO-12",
                      mode: Annotated[Mode, Form()] = "simulation", headers=Depends(mutation_headers)):
        raw = {}
        for name, upload in (("computers.csv", computers_file), ("components.csv", components_file)):
            content = await upload.read(MAX_FILE_BYTES + 1)
            if len(content) > MAX_FILE_BYTES:
                raise Problem(413, "FILE_TOO_LARGE", "Each CSV must be at most 1 MiB.")
            try:
                raw[name] = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise Problem(422, "CSV_ENCODING", f"{name}: save the file as UTF-8.") from exc
        file_hashes = {name: sha(value) for name, value in raw.items()}
        with app.state.db.connect() as connection:
            registration = get_registration(connection, registration_id)
            batch_id = sha(dump({"registration_hash": registration["registration_hash"], "fleet_id": fleet_id, "mode": mode, "file_hashes": file_hashes}))
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
            if existing and existing["committed_revision"] is not None:
                return batch_public(existing)
            fleet = connection.execute("SELECT * FROM fleets WHERE id=?", (fleet_id,)).fetchone()
            if fleet and (fleet["registration_id"] != registration_id or fleet["mode"] != mode):
                raise Problem(409, "FLEET_REGISTRATION_CONFLICT", "A fleet is pinned to one registration and mode; use a new fleet ID.")
            report = validate_csv_pair(connection, registration, fleet_id, mode, raw["computers.csv"], raw["components.csv"])
            payload = {"texts": raw, "file_hashes": file_hashes, "inspection_rule_version": registration["inspection_rule_version"]}
            if existing:
                connection.execute("UPDATE batches SET report=?,preview_revision=?,created_at=? WHERE id=?", (dump(report), fleet["revision"] if fleet else 0, now(), batch_id))
            else:
                connection.execute("INSERT INTO batches (id,registration_id,fleet_id,mode,payload,report,preview_revision,created_at) VALUES (?,?,?,?,?,?,?,?)",
                                   (batch_id, registration_id, fleet_id, mode, dump(payload), dump(report), fleet["revision"] if fleet else 0, now()))
            row = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
            connection.commit()
            return batch_public(row)

    @app.get("/api/v1/imports/{batch_id}")
    def get_batch(batch_id: str):
        with app.state.db.connect() as connection:
            row = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
            if not row:
                raise Problem(404, "BATCH_NOT_FOUND", "Create a new CSV preview.")
            return batch_public(row)

    @app.post("/api/v1/imports/{batch_id}/commit")
    def commit(batch_id: str, body: CommitBody, headers=Depends(mutation_headers)):
        actor, key = headers
        request_hash = sha(dump({"batch_id": batch_id, **body.model_dump()}))
        with app.state.db.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prior_key = connection.execute("SELECT * FROM commit_keys WHERE key=?", (key,)).fetchone()
            if prior_key and (prior_key["request_hash"] != request_hash or prior_key["batch_id"] != batch_id):
                raise Problem(409, "IDEMPOTENCY_CONFLICT", "This commit key belongs to a different request. Reuse the original request or a new key.")
            batch = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
            if not batch:
                raise Problem(404, "BATCH_NOT_FOUND", "Preview both files before committing.")
            if body.preview_hash != batch_id:
                raise Problem(409, "PREVIEW_HASH_MISMATCH", "The files or preview hash changed; create a new preview.")
            if batch["committed_revision"] is not None:
                connection.execute("INSERT OR IGNORE INTO commit_keys VALUES (?,?,?)", (key, batch_id, request_hash))
                connection.commit()
                return batch_public(batch)
            registration = get_registration(connection, batch["registration_id"])
            payload = json.loads(batch["payload"])
            if {name: sha(text) for name, text in payload["texts"].items()} != payload["file_hashes"]:
                raise Problem(409, "BATCH_CONTENT_CONFLICT", "Stored preview content does not match its hashes; create a new preview.")
            calculated = sha(dump({"registration_hash": registration["registration_hash"], "fleet_id": batch["fleet_id"], "mode": batch["mode"], "file_hashes": payload["file_hashes"]}))
            if calculated != batch_id:
                raise Problem(409, "BATCH_CONTENT_CONFLICT", "Stored preview no longer matches its registration.")
            report = validate_csv_pair(connection, registration, batch["fleet_id"], batch["mode"], payload["texts"]["computers.csv"], payload["texts"]["components.csv"])
            if not report["valid"]:
                raise Problem(422, "IMPORT_INVALID", "Fix the row errors and preview both files again.", report["errors"])
            fleet = connection.execute("SELECT * FROM fleets WHERE id=?", (batch["fleet_id"],)).fetchone()
            revision = fleet["revision"] if fleet else 0
            if body.expected_revision != revision or revision != batch["preview_revision"]:
                raise Problem(409, "STALE_PREVIEW", "Fleet changed after preview. Preview the current files again.", revision=revision)
            if fleet and (fleet["registration_id"] != batch["registration_id"] or fleet["mode"] != batch["mode"]):
                raise Problem(409, "FLEET_REGISTRATION_CONFLICT", "Fleet registration/mode changed.")
            imported_at = now()
            try:
                if not fleet:
                    connection.execute("INSERT INTO fleets VALUES (?,?,?,?,0)", (batch["fleet_id"], registration["manifest"]["owner_id"], batch["mode"], batch["registration_id"]))
                for kind, items, csv_name in (("computer", report["computers"], "computers.csv"), ("component", report["components"], "components.csv")):
                    matching = payload["file_hashes"][csv_name] == registration["file_hashes"][csv_name]
                    for item in items:
                        item = {k: v for k, v in item.items() if k != "_row"}
                        subject_id = item["asset_id" if kind == "computer" else "component_id"]
                        assessment_id = sha(batch_id + ":" + kind + ":" + subject_id)
                        evidence = assessment_for(item, kind, registration, matching, imported_at, actor)
                        connection.execute("INSERT INTO assessments VALUES (?,?,?,?,?)", (assessment_id, kind, subject_id, batch_id, dump(evidence)))
                        if kind == "computer":
                            connection.execute("INSERT INTO computers VALUES (?,?,?,?,?,?,?)", (subject_id, batch["fleet_id"], batch["registration_id"], item["board_profile_id"], batch_id, assessment_id, dump(item)))
                        else:
                            location = item["location_asset_id"] or None
                            connection.execute("INSERT INTO components VALUES (?,?,?,?,?,?,?,?)", (subject_id, batch["fleet_id"], batch["registration_id"], batch_id, assessment_id, location, location, dump(item)))
                connection.execute("UPDATE fleets SET revision=? WHERE id=?", (revision + 1, batch["fleet_id"]))
                connection.execute("UPDATE batches SET committed_revision=?, committed_at=?, committed_by=? WHERE id=?", (revision + 1, imported_at, actor, batch_id))
                connection.execute("INSERT INTO commit_keys VALUES (?,?,?)", (key, batch_id, request_hash))
                connection.execute("INSERT INTO audit_events (action,entity_id,actor,occurred_at,data) VALUES (?,?,?,?,?)", ("inventory_imported", batch_id, actor, imported_at, dump({"revision": revision + 1, "counts": report["counts"]})))
                result = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
                connection.commit()
                return batch_public(result)
            except sqlite3.IntegrityError as exc:
                raise Problem(409, "IMPORT_CONFLICT", "Import rolled back completely because a database constraint failed. Refresh inventory and safely retry or preview corrected files.") from exc

    @app.get("/api/v1/state")
    def state(fleet_id: str = "RG-DEMO-12"):
        with app.state.db.connect() as connection:
            computers, components = inventory(connection, fleet_id)
            fleet = connection.execute("SELECT * FROM fleets WHERE id=?", (fleet_id,)).fetchone()
            counts = {"computers": len(computers), "components": len(components),
                      **{key: sum(c["usability"]["classification"] == key for c in computers) for key in ("usable", "unusable", "unknown")},
                      "healthy_components": sum(c["health"] == "healthy" for c in components),
                      "stock_components": sum(not c["location_asset_id"] for c in components)}
            from .recovery import recovery_summary
            optimization, recovery = recovery_summary(connection, fleet_id)
            return {"fleet_id": fleet_id, "mode": fleet["mode"] if fleet else "simulation", "revision": fleet["revision"] if fleet else 0,
                    "registration_id": fleet["registration_id"] if fleet else None, "counts": counts,
                    "optimization": optimization, "recovery": recovery, "rule_version": RULE_VERSION}

    @app.get("/api/v1/computers")
    def computers(fleet_id: str = "RG-DEMO-12", offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        with app.state.db.connect() as connection:
            items, _ = inventory(connection, fleet_id)
            return {"items": items[offset:offset + limit], "total": len(items)}

    @app.get("/api/v1/components")
    def components(fleet_id: str = "RG-DEMO-12", offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        with app.state.db.connect() as connection:
            _, items = inventory(connection, fleet_id)
            return {"items": items[offset:offset + limit], "total": len(items)}

    @app.get("/api/v1/computers/{asset_id}")
    def computer(asset_id: str, fleet_id: str = "RG-DEMO-12"):
        with app.state.db.connect() as connection:
            items, _ = inventory(connection, fleet_id)
            item = next((c for c in items if c["asset_id"] == asset_id), None)
            if not item:
                raise Problem(404, "ASSET_NOT_FOUND", "Select an imported computer.")
            return item

    @app.get("/api/v1/components/{component_id}")
    def component(component_id: str, fleet_id: str = "RG-DEMO-12"):
        with app.state.db.connect() as connection:
            _, items = inventory(connection, fleet_id)
            item = next((c for c in items if c["component_id"] == component_id), None)
            if not item:
                raise Problem(404, "COMPONENT_NOT_FOUND", "Select an imported component.")
            return item

    @app.get("/api/v1/compatibility")
    def compatibility(target_asset_id: str, fleet_id: str = "RG-DEMO-12", mode: Mode | None = None):
        with app.state.db.connect() as connection:
            computers, components = inventory(connection, fleet_id)
            fleet = connection.execute("SELECT mode FROM fleets WHERE id=?", (fleet_id,)).fetchone()
            effective_mode = mode or (fleet["mode"] if fleet else "simulation")
            target = next((c for c in computers if c["asset_id"] == target_asset_id), None)
            if not target:
                raise Problem(404, "ASSET_NOT_FOUND", "Import inventory and choose a target computer.")
            items = []
            for part in components:
                hardware = part_compatibility(part, target["profile"])
                eligible = eligibility(part, target, effective_mode, hardware, part["assessment"])
                if effective_mode == "physical":
                    eligible["eligible"] = False
                    eligible["reasons"].append(reason("PROFILE_SYNTHETIC_PHYSICAL_EXCLUDED", "Toy synthetic profile is not physical manufacturer evidence."))
                items.append({"component_id": part["component_id"], "type": part["type"], "hardware": hardware, "eligibility": eligible,
                              "evidence_ref": part["evidence_ref"], "profile_evidence_ref": target["profile"]["evidence_ref"]})
            return {"target_asset_id": target_asset_id, "profile": target["profile"], "rule_version": RULE_VERSION,
                    "registration_hash": target["registration_hash"], "inspection_rule_version": target["inspection_rule_version"],
                    "target_base_health": target["base_health"], "items": items}

    @app.post("/api/v1/compatibility/configuration")
    def configuration(body: ConfigurationBody, fleet_id: str = "RG-DEMO-12"):
        with app.state.db.connect() as connection:
            computers, components = inventory(connection, fleet_id)
            target = next((c for c in computers if c["asset_id"] == body.target_asset_id), None)
            parts = {p["component_id"]: p for p in components}
            ids = body.ram_component_ids + [body.storage_component_id]
            if not target or any(p not in parts for p in ids):
                raise Problem(422, "REFERENCE_INVALID", "Target and parts must exist in this fleet.")
            if len(ids) != len(set(ids)) or any(parts[p]["type"] != "ram" for p in body.ram_component_ids) or parts[body.storage_component_id]["type"] != "storage":
                raise Problem(422, "CONFIGURATION_INVALID", "Use distinct RAM IDs and exactly one storage ID.")
            ram = ram_configuration([parts[p] for p in body.ram_component_ids], target["profile"])
            storage = part_compatibility(parts[body.storage_component_id], target["profile"])
            eligibility_checks = [{"component_id": p, **eligibility(parts[p], target, body.mode, part_compatibility(parts[p], target["profile"]), parts[p]["assessment"])} for p in ids]
            target_blockers = []
            if target["base_health"] != "healthy":
                target_blockers.append(reason("BASE_NOT_HEALTHY", f"Target fixed base is {target['base_health']}."))
            if target["assessment"]["assessment_kind"] == "unreviewed_physical_assertion":
                target_blockers.append(reason("BASE_REVIEW_PENDING", "Target physical base assertion is pending human review."))
            if body.mode == "physical":
                target_blockers.append(reason("PROFILE_SYNTHETIC_PHYSICAL_EXCLUDED", "Toy synthetic profile is not physical manufacturer evidence."))
            eligible = not target_blockers and ram["decision"] == storage["decision"] == "compatible" and all(e["eligible"] for e in eligibility_checks)
            return {"ram": ram, "storage": storage, "part_eligibility": eligibility_checks, "eligible_configuration": eligible,
                    "target_base_health": target["base_health"], "target_eligibility_reasons": target_blockers, "rule_version": RULE_VERSION,
                    "note": "Inspection only; this endpoint does not allocate, optimize or reserve parts."}

    from .recovery import install_routes
    install_routes(app, inventory, mutation_headers)
    from .assistant import install_routes as assistant_routes
    assistant_routes(app, mutation_headers)
    return app
