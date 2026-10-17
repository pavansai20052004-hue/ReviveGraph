import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone

from .domain import RULE_VERSION, part_compatibility, ram_configuration

COMPUTER_COLUMNS = "asset_id owner_id board_profile_id base_health provenance".split()
COMPONENT_COLUMNS = "component_id owner_id location_asset_id type ram_generation form_factor capacity_gib capacity_gb speed_mt_s voltage_mv ecc buffered interface health provenance evidence_ref".split()
MAX_FILE_BYTES = 1_048_576
MAX_ROWS = 1000
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class Problem(Exception):
    def __init__(self, status, code, message, errors=None, revision=None):
        self.status, self.code, self.message = status, code, message
        self.errors, self.revision = errors or [], revision


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def register_fixture(db, fixture_root, fixture_id, actor):
    if fixture_id != "revivegraph-synthetic-v1":
        raise Problem(404, "FIXTURE_NOT_FOUND", "Only the disclosed synthetic-v1 fixture is bundled.")
    names = ["manifest.json", "board_profiles.json", "operation_costs.json", "computers.csv", "components.csv", "scenarios.json"]
    try:
        raw = {name: (fixture_root / name).read_bytes() for name in names}
        manifest, boards, costs = [json.loads(raw[name]) for name in names[:3]]
        if any(len(value) > MAX_FILE_BYTES for value in raw.values()):
            raise ValueError("A fixture file exceeds 1 MiB.")
        if manifest["fixture_id"] != fixture_id or type(manifest["fixture_version"]) is not int or manifest["fixture_version"] < 1 or manifest["mode"] != "simulation":
            raise ValueError("Fixture identity/version/mode is invalid.")
        if not ID.fullmatch(manifest["owner_id"]):
            raise ValueError("Fixture owner is invalid.")
        for document in (manifest, boards, costs):
            if not document["provenance"].startswith("synthetic:"):
                raise ValueError("Bundled fixture provenance must be explicit synthetic provenance.")
        if boards["schema_version"] != "toy-board-profiles-v1" or costs["schema_version"] != "operation-costs-v1":
            raise ValueError("Unsupported fixture sidecar schema.")
        if (costs["currency"], costs["cost_unit"], costs["time_unit"]) != ("INR", "paise", "technician_minutes"):
            raise ValueError("Resource units must be integer INR paise and technician minutes.")
        expected_ops = {"prepare_target", "verify_target", "remove_ram", "remove_storage", "install_ram", "install_storage"}
        if set(costs["operations"]) != expected_ops:
            raise ValueError("Incomplete operation catalogue.")
        for operation in costs["operations"].values():
            if any(type(operation[field]) is not int or operation[field] < 0 for field in ("cost_paise", "technician_minutes")):
                raise ValueError("Operation costs/durations must be nonnegative integers.")
        seen = set()
        for profile in boards["profiles"]:
            if not ID.fullmatch(profile["id"]) or profile["id"] in seen or type(profile["version"]) is not int or profile["version"] < 1:
                raise ValueError("Invalid or duplicate profile identity.")
            seen.add(profile["id"])
            if not profile["provenance"].startswith("synthetic:") or not profile["evidence_ref"]:
                raise ValueError("Board profile evidence/provenance is absent.")
            for field in ("ram_voltage_mv", "ram_slots", "max_per_slot_gib", "max_total_gib", "sata_ports", "bays_2_5_inch"):
                value = profile[field]
                if value is not None and (type(value) is not int or value < 0):
                    raise ValueError(f"Invalid board field {field}.")
            for field in ("udimm_non_ecc_unbuffered", "mixed_modules_allowed", "sata_boot_supported", "sata_data_available", "sata_power_available"):
                if profile[field] is not None and type(profile[field]) is not bool:
                    raise ValueError(f"Invalid board flag {field}.")
            for field in ("approved_speeds_mt_s", "allowed_module_counts"):
                value = profile[field]
                if value is not None and (not isinstance(value, list) or not value or any(type(n) is not int or n < 1 for n in value) or len(value) != len(set(value))):
                    raise ValueError(f"Invalid board list {field}.")
            if profile["ram_generation"] not in (None, "DDR3", "DDR4"):
                raise ValueError("Unsupported board RAM generation.")
            if profile["ram_generation"] and profile["ram_voltage_mv"] not in (None, 1500 if profile["ram_generation"] == "DDR3" else 1200):
                raise ValueError("Board voltage contradicts generation.")
            if profile["ram_slots"] is not None and profile["allowed_module_counts"] is not None and any(n > profile["ram_slots"] for n in profile["allowed_module_counts"]):
                raise ValueError("Board module counts exceed slots.")
            if all(profile[k] is not None for k in ("max_total_gib", "max_per_slot_gib", "ram_slots")) and profile["max_total_gib"] > profile["max_per_slot_gib"] * profile["ram_slots"]:
                raise ValueError("Board total exceeds slot capacity.")
        if not seen:
            raise ValueError("At least one board profile is required.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Problem(422, "INVALID_FIXTURE", str(exc)) from exc
    hashes = {name: sha(value) for name, value in raw.items()}
    registration_hash = sha(dump({"file_hashes": hashes, "inspection_rule_version": RULE_VERSION}))
    document = {"manifest": manifest, "board_profiles": boards, "operation_costs": costs, "file_hashes": hashes,
                "registration_hash": registration_hash, "inspection_rule_version": RULE_VERSION}
    registration_id = "reg_" + registration_hash
    with db.connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM registrations WHERE fixture_id=? AND version=?", (fixture_id, manifest["fixture_version"])).fetchone()
        if existing:
            if existing["id"] != registration_id:
                raise Problem(409, "FIXTURE_VERSION_CONFLICT", "This fixture identity/version already has different content. Publish a new fixture version.")
            return registration_public(existing)
        for profile in boards["profiles"]:
            profile_hash = sha(dump(profile))
            existing_profile = connection.execute("SELECT content_hash FROM profile_versions WHERE profile_id=? AND version=?", (profile["id"], profile["version"])).fetchone()
            if existing_profile and existing_profile["content_hash"] != profile_hash:
                raise Problem(409, "PROFILE_VERSION_CONFLICT", f"{profile['id']} v{profile['version']} has conflicting content.")
            connection.execute("INSERT OR IGNORE INTO profile_versions VALUES (?,?,?)", (profile["id"], profile["version"], profile_hash))
        connection.execute("INSERT INTO registrations VALUES (?,?,?,?,?,?)", (registration_id, fixture_id, manifest["fixture_version"], dump(document), now(), actor))
        row = connection.execute("SELECT * FROM registrations WHERE id=?", (registration_id,)).fetchone()
        connection.commit()
        return registration_public(row)


def registration_public(row):
    data = json.loads(row["data"])
    return {"id": row["id"], "fixture_id": row["fixture_id"], "version": row["version"],
            "registration_hash": data["registration_hash"], "file_hashes": data["file_hashes"],
            "inspection_rule_version": data["inspection_rule_version"],
            "profile_count": len(data["board_profiles"]["profiles"]), "created_at": row["created_at"],
            "owner_id": data["manifest"]["owner_id"], "mode": data["manifest"]["mode"]}


def get_registration(connection, registration_id):
    row = connection.execute("SELECT * FROM registrations WHERE id=?", (registration_id,)).fetchone()
    if not row:
        raise Problem(422, "REGISTRATION_REQUIRED", "Register the fixture before previewing inventory.")
    registration = json.loads(row["data"])
    if registration.get("inspection_rule_version") != RULE_VERSION:
        raise Problem(409, "RULE_VERSION_MISMATCH", "The registered inspection version differs from this backend. Use the matching backend/rules; do not silently reinterpret inventory.")
    return registration


def parse_csv(text, name, columns, errors):
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff"), newline=""), strict=True)
        if reader.fieldnames != columns:
            errors.append({"file": name, "row": 1, "field": "header", "code": "CSV_HEADER", "message": "Expected columns in order: " + ",".join(columns)})
            return []
        rows = []
        for index, row in enumerate(reader, 2):
            if len(rows) >= MAX_ROWS:
                errors.append({"file": name, "row": index, "field": "file", "code": "ROW_LIMIT", "message": f"At most {MAX_ROWS} records per file."})
                break
            if None in row or any(value is None for value in row.values()):
                errors.append({"file": name, "row": index, "field": "row", "code": "CSV_COLUMNS", "message": "Row has missing or extra columns."})
                continue
            row = {key: value.strip() for key, value in row.items()}
            if any(len(value) > 500 for value in row.values()):
                errors.append({"file": name, "row": index, "field": "row", "code": "CELL_LIMIT", "message": "Cells must contain at most 500 characters."})
                continue
            rows.append({**row, "_row": index})
        return rows
    except csv.Error as exc:
        errors.append({"file": name, "row": 0, "field": "file", "code": "CSV_PARSE", "message": str(exc)})
        return []


def validate_csv_pair(connection, registration, fleet_id, mode, computer_text, component_text):
    errors = []
    computers = parse_csv(computer_text, "computers.csv", COMPUTER_COLUMNS, errors)
    components = parse_csv(component_text, "components.csv", COMPONENT_COLUMNS, errors)
    profiles = {p["id"]: p for p in registration["board_profiles"]["profiles"]}
    owner_id = registration["manifest"]["owner_id"]

    def error(file, row, field, code, message):
        errors.append({"file": file, "row": row.get("_row", 0), "field": field, "code": code, "message": message})

    if not computers or not components:
        errors.append({"file": "batch", "row": 0, "field": "files", "code": "EMPTY_INPUT", "message": "Both CSV files must contain at least one data row."})
    for rows, key, file, table in ((computers, "asset_id", "computers.csv", "computers"), (components, "component_id", "components.csv", "components")):
        seen = set()
        for row in rows:
            if not ID.fullmatch(row[key]):
                error(file, row, key, "INVALID_ID", "Use 1–64 ASCII letters, digits, hyphens or underscores.")
            if row[key] in seen:
                error(file, row, key, "DUPLICATE_ID", "The physical ID occurs more than once in this file.")
            seen.add(row[key])
            if connection.execute(f"SELECT id FROM {table} WHERE id=?", (row[key],)).fetchone():
                error(file, row, key, "EXISTING_ID", "ID already exists; CSV v1 cannot update existing inventory.")
            if row["owner_id"] != owner_id:
                error(file, row, "owner_id", "OWNER_MISMATCH", f"This fixture registration belongs to {owner_id}.")
            if not row["provenance"].startswith(("synthetic:", "physical:")):
                error(file, row, "provenance", "PROVENANCE_REQUIRED", "Use explicit synthetic: or physical: source provenance.")
            if mode == "physical" and row["provenance"].startswith("synthetic:"):
                error(file, row, "provenance", "SYNTHETIC_PHYSICAL_EXCLUDED", "Synthetic assertions cannot be imported into physical inventory.")
    for row in computers:
        if row["board_profile_id"] not in profiles:
            error("computers.csv", row, "board_profile_id", "PROFILE_NOT_REGISTERED", "Reference a profile in this exact registered rule version.")
        if row["base_health"] not in ("healthy", "faulty", "unknown"):
            error("computers.csv", row, "base_health", "HEALTH_ENUM", "Expected healthy, faulty or unknown.")
    assets = {row["asset_id"]: row for row in computers}
    for row in components:
        if row["type"] not in ("ram", "storage"):
            error("components.csv", row, "type", "TYPE_ENUM", "Only ram and storage are supported.")
        if row["health"] not in ("healthy", "faulty", "unknown"):
            error("components.csv", row, "health", "HEALTH_ENUM", "Expected healthy, faulty or unknown.")
        if not row["evidence_ref"]:
            error("components.csv", row, "evidence_ref", "EVIDENCE_REQUIRED", "Supply the source assertion's evidence reference.")
        location = row["location_asset_id"]
        if location and location not in assets:
            error("components.csv", row, "location_asset_id", "LOCATION_NOT_IN_BATCH", "Installed locations must reference a computer in this batch; blank means stock.")
        for field in ("capacity_gib", "capacity_gb", "speed_mt_s", "voltage_mv"):
            value = row[field]
            if value and (not re.fullmatch(r"[0-9]+", value) or int(value) <= 0 or len(value) > 9):
                error("components.csv", row, field, "POSITIVE_INTEGER", "Use a positive integer in documented units, or blank for unknown.")
                row[field] = None
            else:
                row[field] = int(value) if value else None
        for field in ("ecc", "buffered"):
            value = row[field]
            if value not in ("", "true", "false"):
                error("components.csv", row, field, "BOOLEAN", "Use true, false or blank for unknown.")
            row[field] = None if value == "" else value == "true"
        if row["type"] == "ram" and (row["capacity_gb"] is not None or row["interface"]):
            error("components.csv", row, "type", "TYPE_FIELDS", "RAM must leave capacity_gb/interface empty.")
        if row["type"] == "storage" and any(row[f] not in (None, "") for f in ("ram_generation", "capacity_gib", "speed_mt_s", "voltage_mv", "ecc", "buffered")):
            error("components.csv", row, "type", "TYPE_FIELDS", "Storage must leave RAM-specific fields empty.")
        for field in ("ram_generation", "form_factor", "interface"):
            row[field] = row[field] or None
    if not errors:
        for asset, computer in assets.items():
            profile = profiles[computer["board_profile_id"]]
            installed = [part for part in components if part["location_asset_id"] == asset]
            ram = [p for p in installed if p["type"] == "ram"]
            if ram:
                check = ram_configuration(ram, profile)
                for issue in check["reasons"]:
                    if check["decision"] == "incompatible" and issue["code"] != "RAM_POLICY_MIN" and not issue["code"].endswith("UNKNOWN"):
                        error("computers.csv", computer, "board_profile_id", "INSTALLED_LAYOUT", issue["message"])
            for part in installed:
                check = part_compatibility(part, profile)
                if check["decision"] == "incompatible":
                    error("components.csv", part, "location_asset_id", "INSTALLED_INCOMPATIBLE", "; ".join(r["message"] for r in check["reasons"]))
            bays = profile.get("bays_2_5_inch")
            ports = profile.get("sata_ports")
            drives = sum(p["type"] == "storage" for p in installed)
            if (bays is not None and drives > bays) or (ports is not None and drives > ports):
                error("computers.csv", computer, "board_profile_id", "STORAGE_LAYOUT", "Installed drives exceed declared bays or SATA ports.")
    return {"valid": not errors, "errors": errors, "counts": {"computers": len(computers), "components": len(components)},
            "computers": computers, "components": components}


def assessment_for(row, kind, registration, matching_source, imported_at, actor):
    synthetic = row["provenance"].startswith("synthetic:")
    context = registration["manifest"].get("assessment_record_context", {}) if matching_source and synthetic else {}
    return {
        "subject_type": kind, "subject_id": row["asset_id" if kind == "computer" else "component_id"],
        "health": row["base_health" if kind == "computer" else "health"],
        "assessment_kind": "authored_synthetic_assertion" if synthetic else "unreviewed_physical_assertion",
        "provenance": row["provenance"], "source": context.get("source"),
        "evidence_ref": row.get("evidence_ref"),
        "recorded_value": context.get("recorded_date"), "recorded_precision": "date" if context.get("recorded_date") else "unknown",
        "supplied_author_label": context.get("reviewer"),
        "human_reviewer": None, "human_reviewed": False,
        "acceptance_scope": "simulation-only" if synthetic else "pending-physical-review",
        "imported_at": imported_at, "imported_by": actor,
        "context_source": "hash-matched fixture manifest" if context else "CSV assertion only; author/source date not supplied",
    }
