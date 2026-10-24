"""Optional official Adaption SDK workflow. Estimate and paid launch are separate commands."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from revivegraph.explanation_examples import SOURCE, canonical, digest, package, read_json, score_predictions, source_rows

SDK_VERSION = '0.15.0'
MAX_DOWNLOAD = 524288


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def evidence_path(value):
    path = Path(value).resolve()
    base = (ROOT/'data/adaption').resolve()
    if not path.is_relative_to(base) or path==base:
        raise ValueError('Evidence must be a named directory under data/adaption.')
    return path


def save(path, value):
    # Only explicitly selected metadata is passed here; provider exceptions/bodies are never logged.
    raw = (canonical(value)+'\n').encode()
    secret = os.environ.get('ADAPTION_API_KEY')
    if secret and secret.encode() in raw:
        raise ValueError('Refusing to write credential-bearing evidence.')
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,199}',value):
        raise ValueError('Unsupported provider identifier.')
    if value.startswith('pt_live_'):
        raise ValueError('Credential is not an identifier.')
    return value


def number(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise ValueError('Provider returned an invalid nonnegative number.')
    return value


class BudgetClock:
    def __init__(self, seconds=180, clock=time.monotonic, sleep=time.sleep):
        if type(seconds) is not int or not 1<=seconds<=600:
            raise ValueError('Timeout must be 1–600 seconds.')
        self.clock,self.sleep,self.deadline = clock,sleep,clock()+seconds

    def remaining(self):
        remaining = self.deadline-self.clock()
        if remaining<=0:
            raise TimeoutError('Local waiting deadline reached; no remote cancellation is implied.')
        return min(30,remaining)

    def call(self, method, *args, **kwargs):
        return method(*args,timeout=self.remaining(),**kwargs)

    def pause(self):
        self.sleep(min(2,self.remaining()))


def make_client():
    # Deliberately does not read .env, .env.onsite, CLI arguments or a credential file.
    key = os.environ.get('ADAPTION_API_KEY')
    if not key:
        raise ValueError('ADAPTION_API_KEY is missing from this process environment.')
    if version('adaption')!=SDK_VERSION:
        raise ValueError('Install the separately pinned optional Adaption dependencies.')
    import httpx
    from adaption import Adaption
    return Adaption(api_key=key,base_url='https://api.prod.adaptionlabs.ai',max_retries=0,
        timeout=30,http_client=httpx.Client(timeout=30,follow_redirects=False,transport=httpx.HTTPTransport(retries=0)))


def configuration(dataset_hash):
    return {'column_mapping':{'prompt':'prompt','completion':'completion','context':['context','row_id']},
        'recipe_specification':{'recipes':{'prompt_rephrase':True,'deduplication':False,'reasoning_traces':False}},
        'job_specification':{'max_rows':12}, 'training_type':'instruction_dataset', 'language_expansion':None,
        'brand_controls':{'length':'concise','hallucination_mitigation':False,
            'blueprint':('All material is synthetic. Improve the prompt wording for clarity while keeping its scenario and row ID. '
                'Return the completion ONLY as JSON {"fact_ids":[...]} with exactly the existing completion IDs in the same order. '
                'Use the supplied context only. Do not add hardware facts, health scores, prices, physical repairs, approvals or web research. '
                'Keep source row identity available in the export. Source dataset hash: '+dataset_hash)}}


def quote(response):
    if response.estimate is not True or response.run_id is not None:
        raise ValueError('Estimate endpoint did not confirm that no run started.')
    return {'estimated_credits_consumed':number(response.estimated_credits_consumed),
            'estimated_minutes':number(response.estimated_minutes), 'recorded_at':now(), 'estimate_only':True}


def verify_local(receipt):
    manifest,_ = source_rows()
    if (receipt['dataset_hash']!=manifest['dataset_hash'] or receipt['train_file_hash']!=manifest['files']['train.jsonl']
            or receipt['configuration_hash']!=digest(configuration(manifest['dataset_hash']))
            or receipt['configuration']!=configuration(manifest['dataset_hash'])):
        raise ValueError('Source data or run configuration changed. Do not reuse this receipt.')
    return manifest


def estimate(client, directory, timer, put=None):
    """SDK create/complete endpoints are used explicitly to retain the ID before upload."""
    manifest,rows = source_rows()
    directory.mkdir(parents=True,exist_ok=False)
    receipt = {'version':'adaption-explanation-run-v1','synthetic':True,'sdk_version':SDK_VERSION,
        'created_at':now(),'dataset_hash':manifest['dataset_hash'],'train_file_hash':manifest['files']['train.jsonl'],
        'training_rows':len(rows),'heldout_rows_not_uploaded':manifest['holdout_rows'],
        'configuration':configuration(manifest['dataset_hash']),'configuration_hash':digest(configuration(manifest['dataset_hash'])),
        'dataset_id':None,'run_id':None,'run_status':'not_started','evaluation':None,'evaluation_summary':None,
        'actual_credits_consumed':None,'usage_note':'The documented dataset API supplies a quote, not actual billed credits.',
        'retry_policy':'No automatic upload/paid launch retry; inspect an ambiguous attempt before a new directory.'}
    def write(): save(directory/'receipt.json',receipt)
    write()
    try:
        receipt['phase']='creating_dataset'; write()
        created = timer.call(client.datasets.create,source={'file_format':'jsonl','name':'ReviveGraph synthetic explanation examples v1'})
        receipt['dataset_id']=identifier(created.dataset_id); receipt['dataset_created_at']=now(); write()
        instructions = created.upload_instructions
        if not instructions or instructions.method!='PUT':
            raise ValueError('No supported upload instruction returned; stop instead of inventing an API.')
        parsed = urlsplit(instructions.url)
        # The SDK currently calls this an S3 upload. Refuse other storage hosts until reviewed.
        if (parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443)
                or not (parsed.hostname or '').endswith('.amazonaws.com')):
            raise ValueError('Provider upload storage host is unsupported; no upload attempted.')
        raw = (SOURCE/'train.jsonl').read_bytes()
        receipt['phase']='uploading'; write()
        if put is None:
            import httpx
            with httpx.Client(timeout=timer.remaining(),follow_redirects=False,transport=httpx.HTTPTransport(retries=0)) as transport:
                response=transport.put(instructions.url,content=raw)
                response.raise_for_status()
        else:
            put(instructions.url,raw,timer.remaining())
        completed=timer.call(client.datasets.upload.complete_by_id,receipt['dataset_id'],file_size_bytes=len(raw),sha256=digest(raw))
        if completed.dataset_id!=receipt['dataset_id']:
            raise ValueError('Upload completion changed dataset identity.')
        receipt['uploaded_at']=now(); receipt['phase']='ingesting'; write()
        return finish_estimate(client,directory,timer)
    except Exception as exc:
        receipt=read_json(directory/'receipt.json')
        receipt.update(error_type=type(exc).__name__,stopped_at=now()); write()
        raise


def finish_estimate(client,directory,timer):
    """Resume only ingestion/quoting for an already uploaded dataset; never upload or launch."""
    receipt=read_json(directory/'receipt.json')
    verify_local(receipt)
    if (not receipt.get('uploaded_at') or receipt.get('run_id') or (directory/'launch-attempt.json').exists()
            or receipt.get('phase') not in ('ingesting','estimated')):
        raise ValueError('Only a saved, uploaded, unlaunched dataset can be quoted.')
    try:
        dataset=timer.call(client.datasets.get,receipt['dataset_id'])
        if dataset.dataset_id!=receipt['dataset_id'] or dataset.run_id is not None:
            raise ValueError('Dataset already has a run or changed identity; inspect it before quoting.')
        while True:
            status=timer.call(client.datasets.get_status,receipt['dataset_id'])
            if status.dataset_id!=receipt['dataset_id'] or status.status=='failed':
                raise ValueError('Ingestion failed or returned another dataset.')
            receipt['ingestion_status']=status.status
            save(directory/'receipt.json',receipt)
            if status.row_count is not None:
                if type(status.row_count) is not int or status.row_count!=receipt['training_rows']:
                    raise ValueError('Imported row count differs; held-out split must stay excluded.')
                break
            timer.pause()
        q=quote(timer.call(client.datasets.adapt,receipt['dataset_id'],**receipt['configuration'],estimate=True))
        receipt['estimate']=q;receipt['estimate_hash']=digest(q);receipt['phase']='estimated'
        receipt.pop('error_type',None)
        save(directory/'receipt.json',receipt)
        return receipt
    except Exception as exc:
        receipt.update(error_type=type(exc).__name__,stopped_at=now())
        save(directory/'receipt.json',receipt)
        raise


def launch(client,directory,timer,approved_estimate_hash,max_estimated_credits):
    receipt=read_json(directory/'receipt.json')
    verify_local(receipt)
    cap=Decimal(str(max_estimated_credits))
    if not cap.is_finite() or cap<0 or cap>1000:
        raise ValueError('Supply an explicit finite estimated-credit threshold between 0 and 1000.')
    if (receipt.get('phase')!='estimated' or receipt.get('run_id') or receipt.get('estimate_hash')!=approved_estimate_hash
            or digest(receipt.get('estimate'))!=approved_estimate_hash):
        raise ValueError('Approval must name this exact saved estimate; no repeat launch.')
    if Decimal(str(receipt['estimate']['estimated_credits_consumed']))>cap:
        raise ValueError('Saved credit estimate exceeds the approved threshold; no run started.')
    if (directory/'launch-attempt.json').exists():
        raise ValueError('A launch was already attempted. Collect the saved run or inspect the provider; never resubmit automatically.')
    # Requote the identical configuration immediately before the one permitted launch.
    fresh=quote(timer.call(client.datasets.adapt,receipt['dataset_id'],**receipt['configuration'],estimate=True))
    receipt['launch_estimate']=fresh
    save(directory/'receipt.json',receipt)
    if Decimal(str(fresh['estimated_credits_consumed']))>cap:
        raise ValueError('Current estimate exceeds the approved threshold; no run started.')
    run_key='revivegraph-'+uuid.uuid4().hex
    marker={'attempted_at':now(),'dataset_id':receipt['dataset_id'],'configuration_hash':receipt['configuration_hash'],
            'idempotency_key':run_key,'approved_estimate_hash':approved_estimate_hash,'max_estimated_credits':str(cap)}
    # Exclusive marker is durable before the paid SDK method is called.
    with (directory/'launch-attempt.json').open('x',encoding='utf-8') as handle:
        handle.write(canonical(marker))
    receipt['phase']='launch_attempted'; save(directory/'receipt.json',receipt)
    try:
        config={**receipt['configuration'],'job_specification':{**receipt['configuration']['job_specification'],'idempotency_key':run_key}}
        started=timer.call(client.datasets.adapt,receipt['dataset_id'],**config,estimate=False)
        if started.estimate is not False or not started.run_id:
            raise ValueError('Provider did not return a real adaptation handle.')
        receipt.update(run_id=identifier(started.run_id),run_status='pending',started_at=now(),phase='running')
        save(directory/'receipt.json',receipt)
        return collect(client,directory,timer)
    except Exception as exc:
        receipt=read_json(directory/'receipt.json')
        receipt.update(error_type=type(exc).__name__,stopped_at=now())
        save(directory/'receipt.json',receipt)
        raise


def evaluation_data(response):
    status=response.status
    if status not in ('pending','running','succeeded','failed','skipped',None):
        raise ValueError('Unsupported evaluation status.')
    quality=None
    if response.quality is not None:
        quality={}
        for key in ('score_before','score_after','percentile_after','improvement_percent'):
            value=getattr(response.quality,key,None)
            if value is not None:
                # Improvement can be negative; never assume adaptation improved quality.
                if type(value) not in (int,float) or not math.isfinite(value):
                    raise ValueError('Nonfinite evaluation metric.')
                quality[key]=value
        for key in ('grade_before','grade_after'):
            value=getattr(response.quality,key,None)
            if value is not None:
                if value not in ('A','B','C','D','E'):
                    raise ValueError('Unexpected provider grade.')
                quality[key]=value
    return {'status':status,'quality':quality,'retrieved_at':now(),
            'scope':'Adaption-reported dataset quality; not ReviveGraph held-out accuracy, solver improvement or hardware verification.'}


def collect(client,directory,timer):
    receipt=read_json(directory/'receipt.json')
    verify_local(receipt)
    if not receipt.get('run_id'):
        raise ValueError('No saved run handle; inspect an ambiguous launch rather than starting another.')
    try:
        while True:
            status=timer.call(client.datasets.get_status,receipt['dataset_id'])
            if status.dataset_id!=receipt['dataset_id'] or status.status not in ('pending','running','succeeded','failed'):
                raise ValueError('Unexpected adaptation state or dataset identity.')
            receipt['run_status']=status.status; receipt['last_polled_at']=now()
            save(directory/'receipt.json',receipt)
            if status.status=='failed':
                raise ValueError('Adaptation failed; partial output is not accepted.')
            if status.status=='succeeded': break
            timer.pause()
        dataset=timer.call(client.datasets.get,receipt['dataset_id'])
        if dataset.dataset_id!=receipt['dataset_id'] or dataset.run_id!=receipt['run_id']:
            raise ValueError('Downloaded result cannot be bound to the saved run ID; stop for inspection.')
        receipt['completed_at']=now()
        if not (directory/'download.jsonl').exists():
            chunks=[]; size=0
            with client.datasets.with_streaming_response.download(receipt['dataset_id'],file_format='jsonl',timeout=timer.remaining()) as download:
                for chunk in download.iter_bytes(chunk_size=16384):
                    timer.remaining(); size+=len(chunk)
                    if size>MAX_DOWNLOAD: raise ValueError('Downloaded dataset exceeds 512 KiB.')
                    chunks.append(chunk)
            raw=b''.join(chunks)
            # Quarantined provider text is never sent to the application automatically.
            if os.environ.get('ADAPTION_API_KEY','').encode() in raw and os.environ.get('ADAPTION_API_KEY'):
                raise ValueError('Provider output contains credential material.')
            raw.decode('utf-8')
            (directory/'download.jsonl').write_bytes(raw)
            receipt['download_hash']=digest(raw); receipt['downloaded_at']=now()
        elif digest((directory/'download.jsonl').read_bytes())!=receipt.get('download_hash'):
            raise ValueError('Saved provider download changed.')
        # Detect a dashboard/API run that replaced this dataset while export was read.
        current=timer.call(client.datasets.get,receipt['dataset_id'])
        if current.dataset_id!=receipt['dataset_id'] or current.run_id!=receipt['run_id']:
            raise ValueError('Dataset run changed during export; downloaded material stays quarantined.')
        receipt['download_run_id']=current.run_id
        save(directory/'receipt.json',receipt)
        while True:
            evaluation=timer.call(client.datasets.get_evaluation,receipt['dataset_id'])
            if evaluation.dataset_id!=receipt['dataset_id']:
                raise ValueError('Evaluation belongs to another dataset.')
            receipt['evaluation']=evaluation_data(evaluation)
            save(directory/'receipt.json',receipt)
            if evaluation.status in ('succeeded','failed','skipped'):
                break
            timer.pause()
        # Headline summary is optional and may lag the dedicated evaluation endpoint.
        summary=getattr(dataset,'evaluation_summary',None)
        if summary is not None:
            receipt['evaluation_summary']=evaluation_data(type('Summary',(),{'status':'succeeded','quality':summary})())['quality']
        receipt['phase']='collected'; save(directory/'receipt.json',receipt)
        return receipt
    except Exception as exc:
        receipt.update(error_type=type(exc).__name__,stopped_at=now())
        save(directory/'receipt.json',receipt)
        raise


def accept(directory,id_column,prompt_column,completion_column):
    receipt=read_json(directory/'receipt.json'); verify_local(receipt)
    raw=(directory/'download.jsonl').read_bytes()
    if digest(raw)!=receipt.get('download_hash'):
        raise ValueError('Raw download hash changed.')
    if receipt.get('download_run_id')!=receipt.get('run_id'):
        raise ValueError('Download is not bound to the saved run; collect again before acceptance.')
    artifact=package(raw,{'id':id_column,'prompt':prompt_column,'completion':completion_column},receipt)
    path=directory/'accepted-examples.json'
    if path.exists():
        raise ValueError('An accepted artifact already exists; preserve it.')
    save(path,artifact)
    save(directory/'acceptance.json',{'synthetic':True,'accepted_at':now(),'artifact_hash':artifact['artifact_hash'],
        'row_count':len(artifact['rows']),'mapping':{'id':id_column,'prompt':prompt_column,'completion':completion_column},
        'application_enabled':False,'note':'Only exact source fact-ID answers accepted; generated narratives are excluded.'})
    return artifact


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for command in ('estimate','quote','run','collect','accept'):
        p=sub.add_parser(command); p.add_argument('--evidence',required=True)
        p.add_argument('--timeout-seconds',type=int,default=180)
        if command=='run':
            p.add_argument('--approve-paid-run',action='store_true',required=True)
            p.add_argument('--estimate-hash',required=True)
            p.add_argument('--max-estimated-credits',required=True)
        if command=='accept':
            p.add_argument('--id-column',required=True);p.add_argument('--prompt-column',required=True);p.add_argument('--completion-column',required=True)
    p=sub.add_parser('score');p.add_argument('--predictions',required=True)
    args=parser.parse_args()
    client=None
    try:
        if args.command=='score':
            raw=Path(args.predictions).read_bytes()
            if len(raw)>MAX_DOWNLOAD: raise ValueError('Prediction file too large.')
            print(canonical(score_predictions([json.loads(line) for line in raw.splitlines() if line.strip()])))
            return
        directory=evidence_path(args.evidence)
        timer=BudgetClock(args.timeout_seconds)
        if args.command=='accept':
            result=accept(directory,args.id_column,args.prompt_column,args.completion_column)
        else:
            client=make_client()
            if args.command=='estimate':result=estimate(client,directory,timer)
            elif args.command=='quote':result=finish_estimate(client,directory,timer)
            elif args.command=='run':result=launch(client,directory,timer,args.estimate_hash,args.max_estimated_credits)
            else:result=collect(client,directory,timer)
        print(canonical({key:result.get(key) for key in ('dataset_id','run_id','phase','run_status','estimate','estimate_hash','evaluation','artifact_hash')}))
    except Exception as exc:
        # Never print exception text, HTTP body, auth header or signed upload URL.
        print('Adaption step stopped ('+type(exc).__name__+'). No automatic paid retry. Check saved sanitized receipt and setup documentation.',file=sys.stderr)
        raise SystemExit(2)
    finally:
        if client is not None: client.close()


if __name__=='__main__':
    main()
