"""Optional synthetic Adaption examples. Never a source of current hardware facts."""
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'datasets/explanation-synthetic-v1'
VERSION = 'adaption-explanation-examples-v1'
MAX_BYTES = 524288
MAX_PROMPT = 6000
MAX_EXAMPLE_BYTES = 32768


def selection(value):
    """Normalize only a complete JSON code fence; never strip arbitrary prose."""
    normalized=False
    if isinstance(value,str):
        text=value.strip()
        if text.startswith('```json\n') and text.endswith('\n```'):
            text=text[8:-4].strip();normalized=True
        value=json.loads(text)
    return value,normalized


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw if isinstance(raw,bytes) else canonical(raw).encode()).hexdigest()


def read_json(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Explanation artifact exceeds size limit.')
    return json.loads(path.read_bytes())


def source_rows(folder=SOURCE, split='train'):
    manifest = read_json(folder/'manifest.json')
    unsigned = {k:v for k,v in manifest.items() if k!='dataset_hash'}
    if manifest.get('synthetic') is not True or digest(unsigned)!=manifest['dataset_hash']:
        raise ValueError('Source manifest identity changed.')
    if manifest.get('version')!='synthetic-explanations-v1' or manifest.get('assistant_version')!='grounded-assistant-v1':
        raise ValueError('Unsupported explanation dataset contract.')
    for name, expected in manifest['source_files'].items():
        if Path(name).name!=name or digest((ROOT/'datasets/synthetic-v1'/name).read_bytes())!=expected:
            raise ValueError('Source fixture changed.')
    filename = split+'.jsonl'
    raw = (folder/filename).read_bytes()
    if len(raw)>MAX_BYTES or digest(raw)!=manifest['files'][filename]:
        raise ValueError('Source examples changed.')
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != manifest[split+'_rows'] or len({r['row_id'] for r in rows})!=len(rows):
        raise ValueError('Unexpected source row count/identity.')
    for row in rows:
        context = json.loads(row['context'])
        completion = json.loads(row['completion'])
        ids = [fact['id'] for fact in context['facts']]
        if (row['synthetic'] is not True or row['split']!=split or context.get('synthetic') is not True
                or digest({k:v for k,v in row.items() if k!='row_hash'})!=row['row_hash']
                or set(completion)!={'fact_ids'} or completion['fact_ids']!=ids or len(set(ids))!=len(ids)):
            raise ValueError('Source fact-selection contract changed.')
    return manifest, rows


def package(download, mapping, receipt, folder=SOURCE):
    """Require every training ID and the exact reviewed answer; quarantine other output."""
    manifest, source = source_rows(folder)
    if receipt.get('dataset_hash')!=manifest['dataset_hash'] or receipt.get('run_status')!='succeeded':
        raise ValueError('Run did not succeed for the pinned source dataset.')
    if receipt.get('evaluation',{}).get('status')!='succeeded' or not receipt['evaluation'].get('quality'):
        raise ValueError('Provider evaluation is not complete; leave examples disabled.')
    quality = receipt['evaluation']['quality']
    before,after = quality.get('score_before'),quality.get('score_after')
    if (type(before) not in (int,float) or type(after) not in (int,float)
            or not 0<=before<=after<=10):
        raise ValueError('Completed numeric provider scores must be available and non-degrading before promotion.')
    if len(download)>MAX_BYTES or set(mapping)!={'id','prompt','completion'}:
        raise ValueError('Unsupported export size or explicit column mapping.')
    exported = [json.loads(line) for line in download.splitlines() if line.strip()]
    if len(exported)!=len(source):
        raise ValueError('Export changed row count; no partial or held-out acceptance.')
    originals = {r['row_id']:r for r in source}
    accepted = []
    normalized_count = 0
    for row in exported:
        row_id = row[mapping['id']]
        original = originals.pop(row_id, None)
        if original is None:
            raise ValueError('Unknown, duplicate or held-out row in export.')
        prompt, completion = row[mapping['prompt']], row[mapping['completion']]
        if not isinstance(prompt,str) or not 1<=len(prompt)<=MAX_PROMPT:
            raise ValueError('Adapted prompt must be bounded text.')
        completion,normalized = selection(completion)
        normalized_count += normalized
        if canonical(completion)!=original['completion']:
            raise ValueError('Adapted answer is not the exact reviewed fact-ID selection.')
        known_ids = set(re.findall(r'RG-(?:PC|RAM|SSD)-\d+', original['context']))
        if not set(re.findall(r'RG-(?:PC|RAM|SSD)-\d+',prompt))<=known_ids:
            raise ValueError('Adapted prompt introduces an unrelated hardware ID.')
        accepted.append({'row_id':row_id,'synthetic':True,'prompt':prompt,'context':json.loads(original['context']),
                         'completion':completion,'source_row_hash':original['row_hash']})
    body = {'version':VERSION,'synthetic':True,'label':'Synthetic demo — illustrative examples, never current-plan evidence',
        'dataset_hash':manifest['dataset_hash'],'dataset_id':receipt['dataset_id'],'run_id':receipt['run_id'],
        'download_hash':digest(download),'evaluation':receipt['evaluation'],'json_fence_normalizations':normalized_count,
        'rows':sorted(accepted,key=lambda r:r['row_id'])}
    return {**body,'artifact_hash':digest(body)}


def load_examples(question, evidence):
    """Fail closed to zero examples; the existing Agent37/current-facts gate stays active."""
    configured = os.environ.get('REVIVEGRAPH_ADAPTION_EXAMPLES')
    if not configured:
        return [], {'status':'disabled','examples':0}
    try:
        path = Path(configured).resolve()
        base = (ROOT/'data/adaption').resolve()
        if not path.is_relative_to(base) or path.suffix!='.json':
            raise ValueError('Examples must be an accepted JSON artifact under data/adaption.')
        artifact = read_json(path)
        if artifact.get('version')!=VERSION or artifact.get('synthetic') is not True:
            raise ValueError('Unsupported artifact.')
        body = {k:v for k,v in artifact.items() if k!='artifact_hash'}
        if digest(body)!=artifact['artifact_hash']:
            raise ValueError('Artifact hash changed.')
        manifest, rows = source_rows()
        if artifact['dataset_hash']!=manifest['dataset_hash'] or len(artifact['rows'])!=len(rows):
            raise ValueError('Artifact/source version mismatch.')
        if artifact['evaluation'].get('status')!='succeeded' or not artifact['evaluation'].get('quality'):
            raise ValueError('No completed provider evaluation.')
        quality = artifact['evaluation']['quality']
        before,after = quality.get('score_before'),quality.get('score_after')
        if type(before) not in (int,float) or type(after) not in (int,float) or not 0<=before<=after<=10:
            raise ValueError('Provider metrics do not pass the non-degradation gate.')
        expected = {r['row_id']:r for r in rows}
        known = {f['id'] for f in evidence['facts']}
        tokens = set(re.findall(r'[a-z0-9_-]+',question.lower()))
        candidates = []
        for row in artifact['rows']:
            original = expected.pop(row['row_id'],None)
            if (not original or row['synthetic'] is not True or row['source_row_hash']!=original['row_hash']
                    or canonical(row['completion'])!=original['completion'] or canonical(row['context'])!=original['context']
                    or not isinstance(row['prompt'],str) or not 1<=len(row['prompt'])<=MAX_PROMPT):
                raise ValueError('Adapted example is not bound to its source facts.')
            if set(row['completion']['fact_ids'])<=known:
                score = len(tokens & set(re.findall(r'[a-z0-9_-]+', row['prompt'].lower())))
                candidates.append((score,row['row_id'],row))
        examples = []
        for _,_,row in sorted(candidates,key=lambda t:(-t[0],t[1])):
            candidate = {'synthetic':True,'prompt':row['prompt'],'reference_context':row['context'], 'completion':row['completion']}
            if len(canonical(examples+[candidate]).encode('utf-8'))<=MAX_EXAMPLE_BYTES:
                examples.append(candidate)
            if len(examples)==2: break
        return examples, {'status':'accepted','examples':len(examples),'serialized_bytes':len(canonical(examples).encode('utf-8')),'artifact_hash':artifact['artifact_hash'],
                          'dataset_id':artifact['dataset_id'],'run_id':artifact['run_id']}
    except (OSError,ValueError,KeyError,TypeError,AttributeError,RecursionError):
        return [], {'status':'unavailable_or_rejected','examples':0}


def score_predictions(predictions, folder=SOURCE):
    """Offline held-out selection metrics; supplied predictions are not generated here."""
    _, held = source_rows(folder,'holdout')
    if len(predictions)!=len(held) or {p['row_id'] for p in predictions}!={r['row_id'] for r in held}:
        raise ValueError('Supply exactly one labelled prediction for every held-out row.')
    by_id = {p['row_id']:p for p in predictions}
    exact = unsupported = malformed = 0
    for row in held:
        predicted = by_id[row['row_id']].get('fact_ids')
        if not isinstance(predicted,list) or not predicted or any(not isinstance(i,str) for i in predicted) or len(set(predicted))!=len(predicted):
            malformed += 1
            continue
        expected = json.loads(row['completion'])['fact_ids']
        known = {f['id'] for f in json.loads(row['context'])['facts']}
        unsupported += bool(set(predicted)-known)
        exact += predicted == expected
    return {'synthetic':True,'rows':len(held),'exact_selection_accuracy':exact/len(held),
            'unsupported_id_rate':unsupported/len(held),'malformed_output_rate':malformed/len(held),
            'scope':'Only supplied synthetic held-out predictions; no physical/solver/model-quality claim beyond these cases.'}
