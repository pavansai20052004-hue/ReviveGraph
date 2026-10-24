"""Reproducible synthetic explanation examples; never solver input or physical evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from revivegraph.domain import RULE_VERSION, eligibility, part_compatibility, usability
from validate_synthetic_fixture import validate_inventory, evaluate_plan, tiny_oracle

VERSION = 'synthetic-explanations-v1'
OUTPUT = ROOT / 'datasets/explanation-synthetic-v1'
FIXTURE = ROOT / 'datasets/synthetic-v1'
LABEL = 'Synthetic demo — illustrative data; no physical measurements or repairs.'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw if isinstance(raw, bytes) else raw.encode()).hexdigest()


def build():
    manifest, computers, parts, profiles, costs, scenarios = validate_inventory(FIXTURE)
    # Use the existing preparation oracle to recheck each declared scenario.
    # This does not run, replace or modify the production optimizer.
    small = {}
    for case in scenarios['small_cases']:
        best, greedy = tiny_oracle(case, computers, parts, profiles, costs)
        if best != case['expected_max_recoveries'] or ('expected_greedy_recoveries' in case and greedy != case['expected_greedy_recoveries']):
            raise ValueError('Preparation scenario no longer validates: ' + case['id'])
        small[case['id']] = {**case, 'oracle_maximum': best, 'oracle_greedy': greedy}
    main = scenarios['main_fleet']
    failure = main['donor_failure']['component_id']
    main_totals = {}
    for name in ('before_failure', 'after_failure'):
        sample = main[name]
        counts, cash, minutes = evaluate_plan(sample['allocations'], computers, parts, profiles, costs,
            main['budget_paise'], main['technician_minutes'], failure if name == 'after_failure' else None)
        if dict(counts) != sample['expected_operation_counts'] or cash != sample['expected_total_cost_paise'] or minutes != sample['expected_total_technician_minutes']:
            raise ValueError('Documented feasible allocation accounting changed.')
        main_totals[name] = {'cost_paise': cash, 'technician_minutes': minutes, 'operation_counts': dict(counts)}
    numeric = {'capacity_gib','capacity_gb','speed_mt_s','voltage_mv'}
    typed = {}
    for key, source in parts.items():
        part = {k: (int(v) if k in numeric and v else v == 'true' if k in ('ecc','buffered') and v else v or None) for k, v in source.items()}
        part['assessment'] = {'assessment_kind': 'authored_synthetic_assertion', 'evidence_ref': source['evidence_ref'],
                              'human_reviewed': False, 'source': manifest['assessment_record_context']['source']}
        typed[key] = part
    rows = []
    boundary = 'All health assertions, profiles, prices and durations are synthetic. Physical repairs remain zero. No technician review or diagnostic measurement is established.'
    holdout = {'RG-PC-03','RG-PC-08','RG-PC-10','RG-PC-12'}
    candidates = {'RG-PC-05':'RG-SSD-16', 'RG-PC-06':'RG-RAM-11', 'RG-PC-09':'RG-SSD-10', 'RG-PC-11':'RG-RAM-07'}
    def add(row_id, prompt, sections, facts, extra, split='train'):
        context = {'synthetic': True, 'label': LABEL, 'row_id': row_id, 'source_scope':'validated fixture/preparation scenarios; not a computed production plan',
                   **sections, 'facts': facts, **extra}
        row = {'row_id': row_id, 'split': split, 'synthetic': True, 'prompt': prompt,
               'context': canonical(context), 'completion': canonical({'fact_ids':[f['id'] for f in facts]}),
               'provenance': 'synthetic:deterministically-authored-from-validated-synthetic-v1'}
        row['row_hash'] = sha(canonical(row))
        rows.append(row)
    for asset_id, computer in sorted(computers.items()):
        profile = profiles[computer['board_profile_id']]
        installed = [p for p in typed.values() if p['location_asset_id'] == asset_id]
        candidate_id = candidates.get(asset_id) or next((p['component_id'] for p in installed if p['health'] != 'healthy'), installed[0]['component_id'])
        candidate = typed[candidate_id]
        hardware = part_compatibility(candidate, profile)
        eligible = eligibility(candidate, computer, 'simulation', hardware, candidate['assessment'])
        state = usability(computer, installed, profile)
        configuration = f"{asset_id}: {profile['id']}, {profile['ram_generation']} desktop UDIMM; fixed-base assertion {computer['base_health']}; initial usability {state['classification']}. " + '; '.join(r['message'] for r in state['blockers'])
        explanation = f"{candidate['component_id']} hardware is {hardware['decision']}; simulation part eligibility is {eligible['eligible']}. " + '; '.join(r['message'] for r in hardware['reasons']+eligible['reasons']) + ' Part eligibility alone does not establish a recoverable complete target configuration.'
        action = ('Request reviewed evidence for unknown health or decisive profile fields before physical planning. Do not guess missing facts.'
                  if state['classification'] == 'unknown' or candidate['health'] == 'unknown' or hardware['decision'] == 'unknown'
                  else 'Inspect deterministic compatibility and a complete validated simulation plan; obtain explicit review before work. Do not mark any physical repair complete.')
        facts = [{'id':'blockers:'+asset_id,'text':configuration},
                 {'id':f"inspection:{asset_id}:{candidate['component_id']}",'text':explanation},
                 {'id':'simulation-boundary','text':boundary}]
        add('EX-'+asset_id, f"Explain the initial blocker and whether {candidate['component_id']} is a safe candidate for {asset_id}. State uncertainty and the safe next action.",
            {'hardware_configuration_and_blocker':configuration, 'compatibility_explanation':explanation,
             'evidence_uncertainty':boundary, 'recommended_safe_next_action':action}, facts,
            {'hardware':{'computer':computer,'profile':profile,'installed':installed,'candidate':candidate},
             'inspection':{'hardware':hardware,'eligibility':eligible,'usability':state}}, 'holdout' if asset_id in holdout else 'train')
    collective = [
        ('competition','one-physical-part','Why can two targets not both receive the same available drive?',
         'Two targets compete for one physical component. The preparation oracle proves at most one recovery in this restricted case. A part ID cannot be used twice.'),
        ('greedy-trap','greedy-trap','Why compare fleet-wide allocation with a greedy assignment?',
         'The restricted two-target preparation case proves two recoveries versus one for its documented greedy baseline. This does not establish uplift for the full fleet.'),
        ('resource-boundaries','exact-resource-boundary','What should happen at the exact budget/time boundary or with either resource set to zero?',
         'The exact restricted case fits 29000 paise and 38 minutes. The existing zero-budget, zero-time, one-paise-short and one-minute-short cases exclude its sole option; zero never means unlimited.'),
        ('donor-failure',None,'What changes after the documented donor RAM failure before work?',
         f"The preparation example replaces {failure} with RG-RAM-15 for RG-PC-04. Both examples are feasible; no production solver status or fleet optimum is inferred. Physical locations and evidence remain unchanged.")]
    for label, case_id, question, explanation in collective:
        configuration = canonical(small[case_id] if case_id else {'scenario_id':main['id'],'failure':main['donor_failure'],'validated_feasible_totals':main_totals})
        ids = ['resource-limits','simulation-boundary'] if case_id else ['failure-comparison','simulation-boundary']
        add('EX-'+label, question,
            {'hardware_configuration_and_blocker':configuration,'compatibility_explanation':explanation,
             'evidence_uncertainty':boundary,'recommended_safe_next_action':'Review the actual computed current plan and its exact revision. Keep human approval explicit; never use this preparation example as a computed allocation.'},
            [{'id':ids[0],'text':explanation},{'id':ids[1],'text':boundary}],
            {'source_scenario_id':case_id or main['id']})
    train = [r for r in rows if r['split']=='train']
    hold = [r for r in rows if r['split']=='holdout']
    if (len(rows),len(train),len(hold)) != (16,12,4):
        raise ValueError('Unexpected explanation split size.')
    files = {'train.jsonl': ''.join(canonical(r)+'\n' for r in train).encode(),
             'holdout.jsonl': ''.join(canonical(r)+'\n' for r in hold).encode()}
    metadata = {'version':VERSION, 'created_date':'2026-10-24', 'synthetic':True, 'label':LABEL,
        'fixture_id':manifest['fixture_id'],'fixture_version':manifest['fixture_version'],'rule_version':RULE_VERSION,
        'assistant_version':'grounded-assistant-v1','train_rows':12,'holdout_rows':4,
        'source_files':{p.name:sha(p.read_bytes()) for p in sorted(FIXTURE.iterdir()) if p.is_file()},
        'files':{name:sha(raw) for name,raw in files.items()},
        'completion_contract':'Select canonical fact IDs; explanatory sections live in context. Generated narrative is not authoritative.',
        'quality_improvement':'unmeasured; provider evaluation and held-out Agent37 comparison have not run'}
    metadata['dataset_hash'] = sha(canonical(metadata))
    files['manifest.json'] = (json.dumps(metadata,indent=2,ensure_ascii=False)+'\n').encode()
    return files


def main():
    files = build()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    check = '--check' in sys.argv
    for name,raw in files.items():
        path = OUTPUT/name
        if check:
            if not path.is_file() or path.read_bytes()!=raw:
                raise SystemExit('Dataset is not reproducible: '+name)
        else:
            if path.exists() and path.read_bytes()!=raw:
                raise SystemExit('Refusing to overwrite a changed versioned dataset: '+name)
            path.write_bytes(raw)
    print('PASS: 16 synthetic examples (12 train, 4 held out); fixture scenarios validated; '+('bytes match' if check else 'files created'))


if __name__ == '__main__':
    main()
