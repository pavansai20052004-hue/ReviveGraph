"""Additive recovery schema. The v1 inventory/evidence tables remain intact."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS recovery_contexts (
 fleet_id TEXT NOT NULL REFERENCES fleets(id), id TEXT NOT NULL, mode TEXT NOT NULL,
 revision INTEGER NOT NULL, failed_ids TEXT NOT NULL, locations TEXT NOT NULL,
 paused INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(fleet_id,id)
);
CREATE TABLE IF NOT EXISTS recovery_plans (
 id TEXT PRIMARY KEY, fleet_id TEXT NOT NULL REFERENCES fleets(id), context_id TEXT NOT NULL,
 context_revision INTEGER NOT NULL, inventory_revision INTEGER NOT NULL,
 status TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recovery_requests (
 key TEXT PRIMARY KEY, request_hash TEXT NOT NULL, response TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recovery_decisions (
 id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES recovery_plans(id),
 decision TEXT NOT NULL, actor TEXT NOT NULL, occurred_at TEXT NOT NULL, input_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recovery_reservations (
 fleet_id TEXT NOT NULL, mode TEXT NOT NULL, context_id TEXT NOT NULL,
 subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
 plan_id TEXT NOT NULL REFERENCES recovery_plans(id),
 PRIMARY KEY(fleet_id,mode,context_id,subject_type,subject_id)
);
CREATE TABLE IF NOT EXISTS recovery_failures (
 id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES recovery_plans(id),
 context_revision INTEGER NOT NULL, component_id TEXT NOT NULL,
 actor TEXT NOT NULL, occurred_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recovery_reconciliations (
 id TEXT PRIMARY KEY, fleet_id TEXT NOT NULL REFERENCES fleets(id),
 source_context_id TEXT NOT NULL, source_revision INTEGER NOT NULL,
 source_plan_id TEXT NOT NULL REFERENCES recovery_plans(id),
 target_context_id TEXT NOT NULL, target_plan_id TEXT REFERENCES recovery_plans(id),
 data TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(fleet_id,source_context_id,source_revision),
 UNIQUE(fleet_id,target_context_id)
);
CREATE TABLE IF NOT EXISTS recovery_orders (
 id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES recovery_plans(id),
 target_asset_id TEXT NOT NULL, status TEXT NOT NULL,
 UNIQUE(plan_id,target_asset_id)
);
CREATE TABLE IF NOT EXISTS recovery_steps (
 id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES recovery_orders(id),
 position INTEGER NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recovery_verifications (
 id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES recovery_orders(id),
 data TEXT NOT NULL, occurred_at TEXT NOT NULL
);
"""
