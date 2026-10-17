export type Reason = { code: string; message: string }
export type Assessment = {
  assessment_kind: string; source: string | null; provenance: string; evidence_ref: string | null;
  recorded_value: string | null; recorded_precision: string; supplied_author_label: string | null;
  human_reviewer: string | null; human_reviewed: boolean; imported_at: string; imported_by: string;
  acceptance_scope: string; context_source: string;
}
export type Profile = {
  id: string; version: number; provenance: string; evidence_ref: string; ram_generation: string | null;
  ram_voltage_mv: number | null; ram_slots: number | null; max_per_slot_gib: number | null;
  max_total_gib: number | null; approved_speeds_mt_s: number[] | null; sata_boot_supported: boolean | null;
}
export type Component = {
  component_id: string; owner_id: string; location_asset_id: string | null; origin_asset_id: string | null;
  type: 'ram' | 'storage'; ram_generation: string | null; capacity_gib: number | null; capacity_gb: number | null;
  speed_mt_s: number | null; voltage_mv: number | null; form_factor: string | null; interface: string | null;
  health: string; evidence_ref: string; provenance: string; assessment: Assessment; registration_id: string; reserved: boolean;
}
export type Computer = {
  asset_id: string; owner_id: string; board_profile_id: string; base_health: string; profile: Profile;
  assessment: Assessment; installed_components: Component[]; registration_id: string; registration_hash: string;
  usability: { classification: string; blockers: Reason[]; policy: string };
}
export type State = {
  fleet_id: string; revision: number; mode: string; registration_id: string | null; rule_version: string;
  counts: Record<'computers' | 'components' | 'usable' | 'unusable' | 'unknown' | 'healthy_components' | 'stock_components', number>;
  optimization: { status: string };
}
export type Registration = { id: string; fixture_id: string; version: number; registration_hash: string; file_hashes: Record<string, string>; profile_count: number }
export type Batch = {
  batch_id: string; preview_hash: string; expected_revision: number; valid: boolean; committed: boolean;
  revision: number | null; counts: { computers: number; components: number }; file_hashes: Record<string, string>;
  errors: { file: string; row: number; field: string; code: string; message: string }[];
  preview: { computers: { asset_id: string; base_health: string; board_profile_id: string }[]; components: { component_id: string; health: string; location_asset_id: string }[] };
}
export type Edge = {
  component_id: string; type: string; evidence_ref: string; profile_evidence_ref: string;
  hardware: { decision: string; reasons: Reason[]; rule_version: string };
  eligibility: { eligible: boolean; reasons: Reason[]; health: string; availability: string; reservation_state: string; mode: string; note: string };
}
export type Compatibility = { target_asset_id: string; target_base_health: string; profile: Profile; registration_hash: string; rule_version: string; items: Edge[] }
export type Configuration = { eligible_configuration: boolean; ram: { decision: string; reasons: Reason[] }; storage: { decision: string; reasons: Reason[] }; target_base_health: string; target_eligibility_reasons: Reason[]; part_eligibility: { component_id: string; eligible: boolean; reasons: Reason[] }[]; note: string }
