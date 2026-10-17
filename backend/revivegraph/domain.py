"""Deterministic inspection rules. No allocation or optimization lives here."""

RULE_VERSION = "desktop-inspection-v1"


def reason(code, message):
    return {"code": code, "message": message}


def decision(failures, unknowns):
    return {
        "decision": "incompatible" if failures else "unknown" if unknowns else "compatible",
        "reasons": failures + unknowns or [reason("SUPPORTED", "Declared hardware fields satisfy the supported rules.")],
        "rule_version": RULE_VERSION,
    }


def part_compatibility(part, profile):
    failures, unknowns = [], []

    def equal(field, expected, code):
        actual = part.get(field)
        if actual is None or expected is None:
            unknowns.append(reason(code + "_UNKNOWN", f"Missing decisive {field} or board declaration."))
        elif actual != expected:
            failures.append(reason(code, f"{field}: part {actual}; board requires {expected}."))

    def limit(field, maximum, code):
        actual = part.get(field)
        if actual is None or maximum is None:
            unknowns.append(reason(code + "_UNKNOWN", f"Missing {field} or board limit."))
        elif actual > maximum:
            failures.append(reason(code, f"{field} {actual} exceeds board limit {maximum}."))

    if part["type"] == "ram":
        equal("ram_generation", profile.get("ram_generation"), "RAM_GENERATION")
        equal("form_factor", "UDIMM", "RAM_FORM")
        equal("voltage_mv", profile.get("ram_voltage_mv"), "RAM_VOLTAGE")
        equal("ecc", False, "RAM_ECC")
        equal("buffered", False, "RAM_BUFFERED")
        flag = profile.get("udimm_non_ecc_unbuffered")
        if flag is None:
            unknowns.append(reason("RAM_BOARD_FORM_UNKNOWN", "Board UDIMM/non-ECC/unbuffered support is unknown."))
        elif not flag:
            failures.append(reason("RAM_BOARD_FORM", "Board does not support the required RAM form."))
        speed, approved = part.get("speed_mt_s"), profile.get("approved_speeds_mt_s")
        if speed is None or approved is None:
            unknowns.append(reason("RAM_SPEED_UNKNOWN", "RAM speed or approved speed list is unknown."))
        elif speed not in approved:
            failures.append(reason("RAM_SPEED", f"{speed} MT/s is not in the approved list {approved}."))
        limit("capacity_gib", profile.get("max_per_slot_gib"), "RAM_PER_SLOT_CAPACITY")
    else:
        equal("form_factor", "2.5-inch", "STORAGE_FORM")
        equal("interface", "SATA", "STORAGE_INTERFACE")
        if part.get("capacity_gb") is None:
            unknowns.append(reason("STORAGE_CAPACITY_UNKNOWN", "Storage capacity is unknown."))
        for field in ("sata_ports", "bays_2_5_inch"):
            if profile.get(field) is None:
                unknowns.append(reason(field.upper() + "_UNKNOWN", f"Board {field} is unknown."))
            elif profile[field] < 1:
                failures.append(reason(field.upper(), f"Board has no available {field}."))
        for field in ("sata_boot_supported", "sata_data_available", "sata_power_available"):
            if profile.get(field) is None:
                unknowns.append(reason(field.upper() + "_UNKNOWN", f"Board {field} is unknown."))
            elif not profile[field]:
                failures.append(reason(field.upper(), f"Board {field} is false."))
    return decision(failures, unknowns)


def ram_configuration(parts, profile):
    failures, unknowns = [], []
    for part in parts:
        result = part_compatibility(part, profile)
        if result["decision"] == "incompatible":
            failures.extend(result["reasons"])
        elif result["decision"] == "unknown":
            unknowns.extend(result["reasons"])
    slots, counts = profile.get("ram_slots"), profile.get("allowed_module_counts")
    if slots is None or counts is None:
        unknowns.append(reason("RAM_SLOTS_UNKNOWN", "Slot count or supported module counts are unknown."))
    elif len(parts) > slots or len(parts) not in counts:
        failures.append(reason("RAM_SLOTS", f"{len(parts)} modules do not fit supported counts {counts} / {slots} slots."))
    capacities = [part.get("capacity_gib") for part in parts]
    maximum = profile.get("max_total_gib")
    if any(capacity is None for capacity in capacities) or maximum is None:
        unknowns.append(reason("RAM_TOTAL_UNKNOWN", "Total RAM capacity or board maximum is unknown."))
    else:
        total = sum(capacities)
        if total > maximum:
            failures.append(reason("RAM_TOTAL_CAPACITY", f"{total} GiB exceeds board total {maximum} GiB."))
        if total < 8:
            failures.append(reason("RAM_POLICY_MIN", f"{total} GiB is below the 8 GiB demo usefulness policy."))
    signatures = {(part.get("capacity_gib"), part.get("speed_mt_s"), part.get("ram_generation"), part.get("voltage_mv")) for part in parts}
    if len(signatures) > 1:
        mixed = profile.get("mixed_modules_allowed")
        (unknowns if mixed is None else failures if not mixed else []).append(
            reason("RAM_MIXED_MODULES", "Mixed modules require explicit profile permission."))
    return decision(failures, unknowns)


def eligibility(part, target, mode, hardware, assessment, reserved=False):
    blockers = []
    if hardware["decision"] != "compatible":
        blockers.append(reason("HARDWARE_" + hardware["decision"].upper(), "Hardware compatibility must be known and compatible."))
    if part["health"] != "healthy":
        blockers.append(reason("HEALTH_" + part["health"].upper(), f"Part health is {part['health']}."))
    if assessment["assessment_kind"] == "unreviewed_physical_assertion":
        blockers.append(reason("HUMAN_REVIEW_REQUIRED", "The physical assertion is pending human review in every eligibility mode."))
    if part["owner_id"] != target["owner_id"]:
        blockers.append(reason("OWNER_MISMATCH", "Owner authorization is absent for this transfer."))
    if reserved:
        blockers.append(reason("RESERVED", "Part is reserved and unavailable."))
    if mode == "physical" and assessment["assessment_kind"] != "human_reviewed_physical_assessment":
        blockers.append(reason("PHYSICAL_REVIEW_REQUIRED", "An authored/imported assertion is not a human-reviewed physical assessment."))
    if mode == "physical" and part["provenance"].startswith("synthetic:"):
        blockers.append(reason("SYNTHETIC_PHYSICAL_EXCLUDED", "Synthetic health is eligible only in simulation."))
    if part["type"] == "storage" and part.get("capacity_gb") is not None and part["capacity_gb"] < 240:
        blockers.append(reason("STORAGE_POLICY_MIN", "Capacity is below the 240 GB demo usefulness policy."))
    return {
        "eligible": not blockers,
        "reasons": blockers,
        "health": part["health"], "owner_authorized": part["owner_id"] == target["owner_id"],
        "availability": "reserved" if reserved else "installed" if part.get("location_asset_id") else "stock",
        "reservation_state": "reserved" if reserved else "not_reserved", "mode": mode,
        "note": "Candidate inspection does not allocate or reserve a part. Installed parts require removal before transfer.",
    }


def usability(computer, parts, profile):
    known, uncertain = [], []
    if computer["base_health"] == "faulty":
        known.append(reason("BASE_FAULTY", "Fixed base assembly is faulty; RAM/storage transfers cannot recover it."))
    elif computer["base_health"] == "unknown":
        uncertain.append(reason("BASE_UNKNOWN", "Fixed base health is unknown."))
    if computer.get("assessment", {}).get("assessment_kind") == "unreviewed_physical_assertion":
        uncertain.append(reason("BASE_REVIEW_PENDING", "Imported physical base assertion is pending human review."))
    ram = [part for part in parts if part["type"] == "ram"]
    drives = [part for part in parts if part["type"] == "storage"]
    if not ram:
        known.append(reason("RAM_MISSING", "No RAM module is installed."))
    else:
        check = ram_configuration(ram, profile)
        if check["decision"] == "incompatible":
            known.extend(check["reasons"])
        elif check["decision"] == "unknown":
            uncertain.extend(check["reasons"])
    if len(drives) != 1:
        known.append(reason("STORAGE_MISSING_OR_LAYOUT", "Exactly one storage device is required."))
    for part in parts:
        if part.get("assessment", {}).get("assessment_kind") == "unreviewed_physical_assertion":
            uncertain.append(reason("PART_REVIEW_PENDING", f"{part['component_id']} physical assertion is pending human review."))
        if part["health"] == "faulty":
            known.append(reason("PART_FAULTY", f"{part['component_id']} is faulty."))
        elif part["health"] == "unknown":
            uncertain.append(reason("PART_HEALTH_UNKNOWN", f"{part['component_id']} health is unknown."))
        if part["type"] == "storage":
            check = part_compatibility(part, profile)
            if check["decision"] == "incompatible":
                known.extend(check["reasons"])
            elif check["decision"] == "unknown":
                uncertain.extend(check["reasons"])
            if part.get("capacity_gb") is not None and part["capacity_gb"] < 240:
                known.append(reason("STORAGE_POLICY_MIN", "Installed storage is below 240 GB."))
    return {"classification": "unusable" if known else "unknown" if uncertain else "usable",
            "blockers": known + uncertain, "policy": "8 GiB RAM + one 240 GB SATA drive + healthy fixed base", "rule_version": RULE_VERSION}
