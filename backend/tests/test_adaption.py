"""Official SDK transports and Adaption client are mocked; tests never spend credits."""
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace as NS

import httpx
import pytest

from revivegraph import explanation_examples as examples
from revivegraph.explanation_examples import canonical, digest, package, source_rows

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('adaption_cli',ROOT/'scripts/adapt_explanations.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


def exported():
    _,rows=source_rows()
    return b''.join((canonical({'row_id':r['row_id'],'enhanced_prompt':r['prompt']+' Explain safely.',
        'enhanced_completion':r['completion']})+'\n').encode() for r in rows)


class FakeDatasets:
    def __init__(self, credits=3, running=False):
        self.credits,self.running=credits,running
        self.calls=[];self.started=False;self.evaluation_calls=0
        self.upload=NS(complete_by_id=self.complete)
        self.with_streaming_response=NS(download=self.download)
    def create(self,**kwargs):
        self.calls.append(('create',kwargs))
        return NS(dataset_id='dataset-mock-only',upload_instructions=NS(method='PUT',url='https://test-bucket.s3.amazonaws.com/mock-signed-url'))
    def complete(self,dataset_id,**kwargs):
        self.calls.append(('complete',kwargs));return NS(dataset_id=dataset_id)
    def get_status(self,dataset_id,**kwargs):
        self.calls.append(('status',kwargs))
        return NS(dataset_id=dataset_id,row_count=12,status='running' if self.started and self.running else 'succeeded' if self.started else 'awaiting_input')
    def adapt(self,dataset_id,**kwargs):
        self.calls.append(('adapt',copy.deepcopy(kwargs)))
        if not kwargs['estimate']:self.started=True
        return NS(estimate=kwargs['estimate'],run_id=None if kwargs['estimate'] else 'run-mock-only',
                  estimated_credits_consumed=self.credits,estimated_minutes=0.1)
    def get(self,dataset_id,**kwargs):
        return NS(dataset_id=dataset_id,run_id='run-mock-only' if self.started else None,evaluation_summary=None)
    def get_evaluation(self,dataset_id,**kwargs):
        self.evaluation_calls+=1
        return NS(dataset_id=dataset_id,status='succeeded',quality=NS(score_before=6.0,score_after=6.5,percentile_after=None,
            improvement_percent=8.3,grade_before='C',grade_after='B'))
    @contextmanager
    def download(self,dataset_id,**kwargs):
        self.calls.append(('download',kwargs))
        yield NS(iter_bytes=lambda **k:iter([exported()]))


def prepared(tmp_path,credits=3):
    datasets=FakeDatasets(credits)
    client=NS(datasets=datasets)
    path=tmp_path/'run'
    receipt=cli.estimate(client,path,cli.BudgetClock(30),put=lambda *a:None)
    return client,path,receipt


def test_dataset_reproducible_synthetic_and_heldout_isolated():
    manifest,train=source_rows();_,held=source_rows(split='holdout')
    assert len(train)==12 and len(held)==4
    assert not {r['row_id'] for r in train}&{r['row_id'] for r in held}
    required={'hardware_configuration_and_blocker','compatibility_explanation','evidence_uncertainty','recommended_safe_next_action'}
    assert all(required<=json.loads(r['context']).keys() for r in train+held)
    assert all('synthetic' in r['provenance'] and r['synthetic'] for r in train+held)
    assert manifest['quality_improvement'].startswith('unmeasured')


def test_estimate_never_launches_and_logs_no_credentials(tmp_path,monkeypatch):
    monkeypatch.setenv('ADAPTION_API_KEY','mock-secret-never-real')
    client,path,receipt=prepared(tmp_path)
    calls=[k for name,k in client.datasets.calls if name=='adapt']
    assert len(calls)==1 and calls[0]['estimate'] is True
    assert receipt['run_id'] is None and receipt['phase']=='estimated'
    assert receipt['estimate']['estimated_credits_consumed']==3
    assert calls[0]['language_expansion'] is None
    assert calls[0]['recipe_specification']['recipes']['reasoning_traces'] is False
    raw=(path/'receipt.json').read_text()
    assert 'mock-secret-never-real' not in raw and 'mock-signed-url' not in raw
    assert receipt['training_rows']==12 and receipt['heldout_rows_not_uploaded']==4


def test_launch_collect_download_metrics_and_accept(tmp_path):
    client,path,receipt=prepared(tmp_path)
    result=cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    assert result['run_id']=='run-mock-only' and result['run_status']=='succeeded'
    assert result['evaluation']['quality']['score_after']==6.5
    assert result['actual_credits_consumed'] is None
    assert result['download_hash']==digest((path/'download.jsonl').read_bytes())
    calls=[k for name,k in client.datasets.calls if name=='adapt']
    assert [c['estimate'] for c in calls]==[True,True,False]
    assert calls[-1]['job_specification']['max_rows']==12
    assert calls[-1]['job_specification']['idempotency_key'].startswith('revivegraph-')
    artifact=cli.accept(path,'row_id','enhanced_prompt','enhanced_completion')
    assert artifact['synthetic'] and len(artifact['rows'])==12
    assert json.loads((path/'acceptance.json').read_text())['application_enabled'] is False
    with pytest.raises(ValueError):cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    with pytest.raises(ValueError):cli.accept(path,'row_id','enhanced_prompt','enhanced_completion')


@pytest.mark.parametrize('kind',['over_cap','changed_quote','wrong_hash','negative_cap'])
def test_approval_and_estimate_guards_no_paid_start(tmp_path,kind):
    client,path,receipt=prepared(tmp_path)
    cap='2' if kind=='over_cap' else '-1' if kind=='negative_cap' else '3'
    if kind=='changed_quote':client.datasets.credits=4
    with pytest.raises(ValueError):
        cli.launch(client,path,cli.BudgetClock(30),'wrong' if kind=='wrong_hash' else receipt['estimate_hash'],cap)
    assert not client.datasets.started
    assert not (path/'launch-attempt.json').exists()


def test_ambiguous_launch_not_repeated(tmp_path):
    client,path,receipt=prepared(tmp_path)
    original=client.datasets.adapt
    def uncertain(dataset_id,**kwargs):
        if kwargs['estimate'] is False:raise httpx.ReadTimeout('mock-only secret-bearing-body must not be persisted')
        return original(dataset_id,**kwargs)
    client.datasets.adapt=uncertain
    with pytest.raises(httpx.ReadTimeout):cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    assert (path/'launch-attempt.json').exists()
    assert 'secret-bearing-body' not in (path/'receipt.json').read_text()
    with pytest.raises(ValueError):cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')


def test_resume_quote_uses_existing_dataset_without_upload_or_launch(tmp_path):
    client,path,receipt=prepared(tmp_path)
    before=len([x for x in client.datasets.calls if x[0]=='create'])
    result=cli.finish_estimate(client,path,cli.BudgetClock(30))
    assert result['dataset_id']==receipt['dataset_id'] and result['phase']=='estimated'
    assert len([x for x in client.datasets.calls if x[0]=='create'])==before
    assert not client.datasets.started


def test_timeout_preserves_run_and_collect_never_relaunches(tmp_path):
    client,path,receipt=prepared(tmp_path)
    client.datasets.running=True
    ticks=[0]
    timer=cli.BudgetClock(1,clock=lambda:ticks[0],sleep=lambda seconds:ticks.__setitem__(0,ticks[0]+seconds))
    with pytest.raises(TimeoutError):cli.launch(client,path,timer,receipt['estimate_hash'],'3')
    saved=json.loads((path/'receipt.json').read_text())
    assert saved['run_id']=='run-mock-only' and saved['run_status']=='running'
    assert saved['error_type']=='TimeoutError'
    client.datasets.running=False
    result=cli.collect(client,path,cli.BudgetClock(30))
    assert result['phase']=='collected'
    assert len([k for n,k in client.datasets.calls if n=='adapt' and not k['estimate']])==1


@pytest.mark.parametrize('kind',['unknown_id','duplicate_row','holdout','wrong_answer','narrative','missing_row','oversized'])
def test_adapted_artifact_rejects_unsupported_examples(tmp_path,kind):
    client,path,receipt=prepared(tmp_path)
    result=cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    rows=[json.loads(line) for line in exported().splitlines()]
    if kind=='unknown_id':rows[0]['row_id']='EX-invented'
    if kind=='duplicate_row':rows[0]=rows[1]
    if kind=='holdout':rows[0]['row_id']='EX-RG-PC-03'
    if kind=='wrong_answer':rows[0]['enhanced_completion']='{"fact_ids":["simulation-boundary"]}'
    if kind=='narrative':rows[0]['enhanced_completion']='Physical computer repaired successfully'
    if kind=='missing_row':rows.pop()
    if kind=='oversized':rows[0]['enhanced_prompt']='x'*6001
    raw=b''.join((canonical(r)+'\n').encode() for r in rows)
    with pytest.raises((ValueError,KeyError)):
        package(raw,{'id':'row_id','prompt':'enhanced_prompt','completion':'enhanced_completion'},result)


def test_optional_runtime_examples_and_fallback(tmp_path,monkeypatch):
    client,path,receipt=prepared(tmp_path)
    cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    artifact=cli.accept(path,'row_id','enhanced_prompt','enhanced_completion')
    # Real file/path/hash checks, with the immutable fixture copied into the isolated root.
    shutil.copytree(ROOT/'datasets/synthetic-v1',tmp_path/'datasets/synthetic-v1')
    monkeypatch.setattr(examples,'ROOT',tmp_path)
    target=tmp_path/'data/adaption/run/accepted-examples.json';target.parent.mkdir(parents=True)
    target.write_text(canonical(artifact),encoding='utf-8')
    ids={i for row in artifact['rows'] for i in row['completion']['fact_ids']}
    evidence={'facts':[{'id':i} for i in ids]}
    monkeypatch.delenv('REVIVEGRAPH_ADAPTION_EXAMPLES',raising=False)
    assert examples.load_examples('blocker',evidence)==([],{'status':'disabled','examples':0})
    monkeypatch.setenv('REVIVEGRAPH_ADAPTION_EXAMPLES',str(target))
    selected,meta=examples.load_examples('blocker',evidence)
    assert len(selected)==2 and meta['status']=='accepted'
    assert meta['serialized_bytes']<=32768
    assert all(set(row['completion']['fact_ids'])<=ids for row in selected)
    monkeypatch.setattr(examples,'MAX_EXAMPLE_BYTES',100)
    small,small_meta=examples.load_examples('blocker',evidence)
    assert small==[] and small_meta['serialized_bytes']<=100
    monkeypatch.setattr(examples,'MAX_EXAMPLE_BYTES',32768)
    artifact['rows'][0]['completion']={'fact_ids':['invented']}
    # Even an internally rehashed local artifact must pass source-answer binding.
    artifact['artifact_hash']=digest({k:v for k,v in artifact.items() if k!='artifact_hash'})
    target.write_text(canonical(artifact),encoding='utf-8')
    assert examples.load_examples('blocker',evidence)[1]['status']=='unavailable_or_rejected'
    monkeypatch.setenv('REVIVEGRAPH_ADAPTION_EXAMPLES',str(path/'outside-allowed-tree.json'))
    assert examples.load_examples('blocker',evidence)[0]==[]


def test_heldout_metrics_count_wrong_known_ids_separately():
    _,held=source_rows(split='holdout')
    predictions=[{'row_id':r['row_id'],**json.loads(r['completion'])} for r in held]
    predictions[0]['fact_ids']=['simulation-boundary'] # Known, but insufficient answer.
    predictions[1]['fact_ids']=['invented']
    predictions[2]['fact_ids']='not a list'
    metrics=examples.score_predictions(predictions)
    assert metrics['exact_selection_accuracy']==0.25
    assert metrics['unsupported_id_rate']==0.25 and metrics['malformed_output_rate']==0.25


@pytest.mark.parametrize('kind',['pending','failed','degraded','missing_scores'])
def test_no_promotion_without_completed_nondegrading_metrics(tmp_path,kind):
    client,path,receipt=prepared(tmp_path)
    result=cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    if kind in ('pending','failed'):result['evaluation']['status']=kind
    if kind=='degraded':result['evaluation']['quality']['score_after']=5
    if kind=='missing_scores':result['evaluation']['quality'].pop('score_after')
    with pytest.raises(ValueError):package(exported(),{'id':'row_id','prompt':'enhanced_prompt','completion':'enhanced_completion'},result)


def test_key_is_environment_only_and_not_read_from_settings(monkeypatch):
    monkeypatch.delenv('ADAPTION_API_KEY',raising=False)
    with pytest.raises(ValueError):cli.make_client()
    assert 'ADAPTION_API_KEY' not in __import__('revivegraph.settings',fromlist=['ALLOWED']).ALLOWED


def test_dataset_run_changed_during_download_blocks_acceptance(tmp_path):
    client,path,receipt=prepared(tmp_path)
    original=client.datasets.get
    def change(dataset_id,**kwargs):
        result=original(dataset_id,**kwargs)
        if client.datasets.started and any(n=='download' for n,_ in client.datasets.calls):
            result.run_id='other-run-mock-only'
        return result
    client.datasets.get=change
    with pytest.raises(ValueError):cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    assert (path/'download.jsonl').exists()
    assert not (path/'accepted-examples.json').exists()


def test_untrusted_storage_host_stops_before_upload(tmp_path):
    client=NS(datasets=FakeDatasets())
    client.datasets.create=lambda **k:NS(dataset_id='dataset-mock-only',upload_instructions=NS(method='PUT',url='http://127.0.0.1/secret'))
    with pytest.raises(ValueError):
        cli.estimate(client,tmp_path/'blocked',cli.BudgetClock(30),put=lambda *a:pytest.fail('Must not upload'))
    receipt=json.loads((tmp_path/'blocked/receipt.json').read_text())
    assert receipt['dataset_id']=='dataset-mock-only' and receipt['run_id'] is None


def test_real_sdk_estimate_serialization_uses_current_adapt_api():
    from adaption import Adaption
    seen=[]
    def respond(request):
        seen.append(request)
        return httpx.Response(200,json={'run_id':None,'estimatedMinutes':0.1,'estimatedCreditsConsumed':3,
            'estimate':True,'multimodalPricingApplied':False})
    client=Adaption(api_key='mock-not-a-real-key',base_url='https://api.prod.adaptionlabs.ai',max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(respond)))
    manifest,_=source_rows()
    try:
        q=cli.quote(client.datasets.adapt('dataset-mock-only',**cli.configuration(manifest['dataset_hash']),estimate=True))
    finally:client.close()
    assert seen[0].url.path=='/api/v1/datasets/dataset-mock-only/adapt'
    body=json.loads(seen[0].content)
    assert body['estimate'] is True and body['job_specification']['max_rows']==12
    assert q['estimated_credits_consumed']==3


@pytest.mark.parametrize('kind',['fence','prose_before','prose_after','nested','6000','6001'])
def test_bounded_provider_format_interoperability(tmp_path,kind):
    client,path,receipt=prepared(tmp_path)
    result=cli.launch(client,path,cli.BudgetClock(30),receipt['estimate_hash'],'3')
    rows=[json.loads(line) for line in exported().splitlines()]
    text=rows[0]['enhanced_completion']
    if kind in ('fence','prose_before','prose_after','nested'):
        text='```json\n'+text+'\n```'
        if kind=='prose_before':text='Here is an answer.\n'+text
        if kind=='prose_after':text+='\nA physical repair passed.'
        if kind=='nested':text='```json\n'+text+'\n```'
        rows[0]['enhanced_completion']=text
    else:rows[0]['enhanced_prompt']='x'*int(kind)
    raw=b''.join((canonical(r)+'\n').encode() for r in rows)
    mapping={'id':'row_id','prompt':'enhanced_prompt','completion':'enhanced_completion'}
    if kind in ('fence','6000'):
        artifact=package(raw,mapping,result)
        assert artifact['json_fence_normalizations']==int(kind=='fence')
    else:
        with pytest.raises(ValueError):package(raw,mapping,result)
