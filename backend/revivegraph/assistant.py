"""Deterministic saved-plan evidence summaries; no external AI transport."""
import json
from fastapi import Depends
from pydantic import Field

from .domain import eligibility, part_compatibility
from .execution_protocol import digest
from .imports import Problem, dump, now, sha
from .optimizer import validate_output
from .recovery import Body, audit, fingerprint, public_plan, request_hash
from .settings import settings

VERSION = "grounded-assistant-v1"


class Question(Body):
    question: str = Field(min_length=1, max_length=1500)
    provider: str = Field(default="facts", max_length=32)
    asset_id: str | None = Field(default=None, max_length=64)


def context(c, plan_id, asset_id=None):
    p = public_plan(c, plan_id)
    if (sha(dump(p["snapshot"])) != p["snapshot_hash"] or request_hash(p) != p["input_hash"]
            or sha(dump(p["result"])) != p["output_hash"]):
        raise Problem(409, "PLAN_INVALID", "Stored plan hashes do not match. Recalculate before explaining it.")
    checked = validate_output(p["snapshot"], p["result"]["allocations"], p["budget_paise"], p["time_minutes"])
    if any(digest(checked[k]) != digest(p["result"][k]) for k in ("totals", "operations")):
        raise Problem(409, "PLAN_INVALID", "Stored allocations fail independent accounting validation.")
    facts = []
    def add(key, text, data):
        facts.append({"id": key, "text": text, "data": data})
    t = checked["totals"]
    add("plan-summary", f"This {p['status']} simulation plan has {t['usable_final']} usable final configurations and {t['newly_recovered']} newly recovered candidates. Estimated operations cost {t['cost_paise']} INR paise and take {t['technician_minutes']} technician minutes. These are synthetic assumptions, not physical repair results.", t)
    add("resource-limits", f"Hard limits are {p['budget_paise']} INR paise and {p['time_minutes']} technician minutes. Remaining headroom is {p['budget_paise']-t['cost_paise']} paise and {p['time_minutes']-t['technician_minutes']} minutes.", {"budget_paise": p["budget_paise"], "time_minutes": p["time_minutes"]})
    runner = p.get("execution", {})
    cpu = "Nodus cloud CPU" if runner.get("provider") == "nodus" else "Render worker CPU" if runner.get("workflow", {}).get("orchestrator") == "render-workflows" else "local CPU"
    add("solver-status", f"The {cpu} solver reports {p['result']['solver']['status']}. Feasibility and operation totals were independently reconstructed. Remote optimality metadata is worker-reported, not re-proven by this assistant.", p["result"]["solver"])
    add("simulation-boundary", "Physical repair totals remain zero. Health assertions and toy profiles are synthetic. AI cannot accept assessments, change hardware compatibility, approve a plan, complete work or verify hardware.", {"physical_repairs": 0})
    if p["status"] in ("stale", "paused", "rejected"):
        add("plan-action-blocked", f"This plan is {p['status']}; its previous approval cannot authorize execution. Review the current revision. Paused simulated work requires explicit reconciliation review and renewed exact-plan approval.", {"status": p["status"]})
    baseline = p["result"].get("baseline", {}).get("totals")
    if baseline:
        add("greedy-comparison", f"The same-input greedy baseline has {baseline['usable_final']} usable final configurations, {baseline['cost_paise']} paise and {baseline['technician_minutes']} minutes. The solver's recovery-count difference is {t['usable_final']-baseline['usable_final']}; no improvement is assumed.", baseline)
    parts = {part["component_id"]: part for part in p["snapshot"]["components"]}
    targets = {target["asset_id"]: target for target in p["snapshot"]["computers"]}
    if asset_id and asset_id not in targets:
        raise Problem(404, "ASSET_NOT_IN_PLAN", "Choose an asset from this plan's pinned snapshot.")
    for allocation in p["result"]["allocations"]:
        target = allocation["target_asset_id"]
        selected_ids = allocation["ram_component_ids"] + [allocation["storage_component_id"]]
        locations = "; ".join(f"{part_id}: {'retained' if parts[part_id]['location_asset_id'] == target else 'incoming from ' + (parts[part_id]['location_asset_id'] or 'stock')}" for part_id in selected_ids)
        add("allocation:" + target, f"{target} uses {', '.join(selected_ids)}. {locations}. Whole-configuration health, ownership, hardware rules and one-use constraints passed the deterministic validator.", allocation)
        if not asset_id or asset_id == target:
            for part_id, part in parts.items():
                if part["type"] != "ram" or part_id in selected_ids or len(allocation["ram_component_ids"]) != 1:
                    continue
                alternative = {**allocation, "ram_component_ids": [part_id]}
                candidate = [alternative if a["target_asset_id"] == target else a for a in p["result"]["allocations"]]
                try:
                    alt = validate_output(p["snapshot"], candidate, p["budget_paise"], p["time_minutes"])["totals"]
                except ValueError:
                    continue
                add(f"alternative:{target}:{part_id}", f"A checked single-RAM alternative for {target} uses {part_id} instead of {allocation['ram_component_ids'][0]}. With all other assignments unchanged it costs {alt['cost_paise']} paise and takes {alt['technician_minutes']} minutes, a change of {alt['cost_paise']-t['cost_paise']} paise and {alt['technician_minutes']-t['technician_minutes']} minutes. This is a feasible comparison, not a new optimized plan.", {"target_asset_id": target, "alternative_component_id": part_id, "totals": alt})
    for target_id, target in targets.items():
        blockers = target.get("usability", {}).get("blockers", [])
        add("blockers:" + target_id, f"{target_id} initial usability is {target.get('usability', {}).get('classification', 'unknown')}. " + ("; ".join(b["code"] + ": " + b["message"] for b in blockers) or "No initial blocker is recorded."), blockers)
    if asset_id:
        target = targets[asset_id]
        for part_id, part in parts.items():
            hardware = part_compatibility(part, target["profile"])
            eligible = eligibility(part, target, "simulation", hardware, part.get("assessment"))
            if part_id in p["snapshot"].get("failed_component_ids", []):
                eligible = {**eligible, "eligible": False, "availability": "scenario_excluded", "reasons": eligible["reasons"] +
                            [{"code": "SCENARIO_FAILED", "message": "Excluded by this scenario's simulated failure."}]}
            reasons = hardware["reasons"] + eligible["reasons"]
            add(f"inspection:{asset_id}:{part_id}", f"{part_id} against {asset_id}: hardware {hardware['decision']}. " + ("; ".join(r["code"] + ": " + r["message"] for r in reasons) or "No hardware/eligibility exclusion recorded; allocation still requires complete configuration and one-use/resource checks."), {"hardware": hardware, "eligibility": eligible, "reasons": reasons})
    comparison = p.get("comparison")
    if comparison:
        add("failure-comparison", "This revision preserves its parent plan. Changed target assignments are recorded explicitly; unchanged totals do not imply unchanged components. " + dump(comparison), comparison)
    return {"version": VERSION, "plan_id": p["id"], "plan_status": p["status"], "input_hash": p["input_hash"], "output_hash": p["output_hash"],
            "facts": facts, "tools": ["read_plan", "validate_allocations", "read_blockers", "inspect_compatibility", "compare_feasible_ram", "read_failure_changes"],
            "mode": "simulation", "physical_repairs": 0}


def select_facts(evidence, asset_id=None):
    """Choose a fixed evidence summary, not an AI answer to the supplied note."""
    selected = ["plan-summary", "resource-limits", "greedy-comparison", "simulation-boundary"]
    if asset_id:
        selected = ["allocation:" + asset_id, "blockers:" + asset_id, "simulation-boundary"]
    if any(f["id"] == "failure-comparison" for f in evidence["facts"]):
        selected.append("failure-comparison")
    return selected


def install_routes(app, headers):
    db = app.state.db
    @app.get("/api/v1/integrations")
    def integrations():
        cfg = settings()
        return {"assistant": {"provider": "facts", "network_requests": False},
                "render": {"configured": bool(cfg.get("RENDER_API_KEY") and cfg.get("REVIVEGRAPH_RENDER_TASK")), "enabled": cfg.get("REVIVEGRAPH_RENDER_ENABLED") == "1"},
                "assistant_version": VERSION}

    @app.get("/api/v1/plans/{plan_id}/assistant-context")
    def facts(plan_id: str, asset_id: str | None = None):
        with db.connect() as c:
            return context(c, plan_id, asset_id)

    @app.post("/api/v1/plans/{plan_id}/assistant")
    def answer(plan_id: str, body: Question, identity=Depends(headers)):
        actor, key = identity
        if body.provider != "facts":
            raise Problem(410, "EXPLANATION_PROVIDER_REMOVED", "External explanation providers have been removed. Choose facts for an explicit local evidence summary; no provider request was made.")
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            evidence = context(c, plan_id, body.asset_id)
            fp = fingerprint("assistant:" + plan_id, {**body.model_dump(), "input_hash": evidence["input_hash"], "output_hash": evidence["output_hash"]}, actor)
            prior = c.execute("SELECT * FROM recovery_requests WHERE key=?", (key,)).fetchone()
            if prior:
                if prior["request_hash"] != fp:
                    raise Problem(409, "IDEMPOTENCY_CONFLICT", "Use this key only for its original question, plan and actor.")
                saved = json.loads(prior["response"])
                if saved.get("pending"):
                    raise Problem(409, "ASSISTANT_ATTEMPT_PENDING", "This summary attempt started but has no accepted response. Review its audit record before using a new key.")
                return saved
            c.execute("INSERT INTO recovery_requests VALUES (?,?,?)", (key, fp, dump({"pending": True})))
            c.commit()
        selected = select_facts(evidence, body.asset_id)
        provider = {"status": "deterministic", "usage": None}
        chosen = [f for i in selected for f in evidence["facts"] if f["id"] == i]
        result = {"version": VERSION, "provider": body.provider, "plan_id": plan_id, "asset_id": body.asset_id, "input_hash": evidence["input_hash"],
                  "output_hash": evidence["output_hash"], "question": body.question, "facts": chosen, "provider_evidence": provider,
                  "recorded_at": now(), "actor": actor, "read_only": True, "physical_repairs": 0,
                  "label": "Local evidence summary \u2014 no AI request"}
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            current = context(c, plan_id, body.asset_id)
            result["plan_status_at_response"] = current["plan_status"]
            if current["input_hash"] != evidence["input_hash"] or current["output_hash"] != evidence["output_hash"]:
                raise Problem(409, "PLAN_CHANGED", "Plan data changed while the assistant was responding.")
            if current["plan_status"] != evidence["plan_status"]:
                raise Problem(409, "PLAN_STATUS_CHANGED", "Plan status changed while the assistant was responding. Its answer was not accepted. Review the latest plan before asking again.")
            audit(c, "assistant_explanation", plan_id, actor, result)
            c.execute("UPDATE recovery_requests SET response=? WHERE key=? AND request_hash=?", (dump(result), key, fp))
            c.commit()
        return result
