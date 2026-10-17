from pathlib import Path
import sys, json, socket
import numpy as np
import pandas as pd
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import disk_model as model
from core.smart_parser import parse
from core.nvme_rules import score
from scripts.prepare_backblaze import prepare
from scripts.train_disk_model import train, split_data
from scripts.make_demo_json import make_demos
from scripts.make_demo_json import sanitized_nvme_capture

@pytest.fixture
def quarter(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir()
    for day in range(1,7):
        rows=[]
        for i in range(40):
            fails=i<16
            if fails and day>4: continue
            rows.append(dict(date=f'2026-04-{day:02d}',serial_number=f'DRIVE-{i:03d}',model='Example HDD',capacity_bytes=1000000000000,failure=int(fails and day==4),smart_5_raw=i+1 if fails else 0,smart_9_raw=1000+i,smart_187_raw=0,smart_188_raw=np.nan,smart_194_raw=35,smart_197_raw=i+2 if fails else 0,smart_198_raw=0))
        pd.DataFrame(rows).to_csv(raw/f'2026-04-{day:02d}.csv',index=False)
    return raw

def test_prior_day_labels_and_followup(quarter,tmp_path):
    frame,meta=prepare(quarter,tmp_path/'sample.csv',healthy_n=24,healthy_days=6)
    assert frame.serial_number.is_unique
    assert set(frame.loc[frame.failure.eq(1),'date'].dt.day)=={3}
    assert set(frame.loc[frame.failure.eq(1),'source_failure'])=={0}
    assert (frame.loc[frame.failure.eq(1),'target_failure_date']-frame.loc[frame.failure.eq(1),'date']).dt.days.eq(1).all()
    assert frame.loc[frame.failure.eq(0),'date'].dt.day.max()<=5
    assert frame.loc[frame.failure.eq(0),'target_failure_date'].isna().all()
    assert frame.smart_188_raw.isna().all()
    assert meta['positive_rows']==16 and meta['negative_rows']==24
    context,test=split_data(frame,6)
    assert not set(context.serial_number)&set(test.serial_number)

def test_actual_rf_journey_without_network(quarter,tmp_path,monkeypatch):
    def deny(*a,**k): raise AssertionError('unexpected network call')
    monkeypatch.setattr(socket.socket,'connect',deny)
    frame,_=prepare(quarter,tmp_path/'sample.csv',healthy_n=24)
    out=tmp_path/'models'; report=tmp_path/'metrics.md'
    meta=train(tmp_path/'sample.csv',method='rf',n_per_class=6,output_dir=out,report=report)
    assert meta['selected']=='rf' and meta['test_n']==10
    make_demos(out,tmp_path/'demo')
    monkeypatch.setenv('DD_CONTEXT_PATH',str(out/'train_context.csv'))
    monkeypatch.setenv('DD_DISK_MODEL','rf')
    monkeypatch.chdir(tmp_path)
    expected={'risk','level','drivers','method'}
    for name in ['healthy_hdd','failing_hdd']:
        payload=json.loads((tmp_path/'demo'/f'{name}.json').read_text(encoding='utf-8'))
        d=parse(payload); r=model.predict(d)
        assert set(r)==expected and 0<=r['risk']<=1 and r['method']=='rf'
        assert payload['_provenance']['lead_days']==1
    nvme=json.loads((tmp_path/'demo/my_nvme.json').read_text())
    assert 'SYNTHETIC' in nvme['_source']
    assert score(parse(nvme))['method']=='nvme_rules'
    before=(out/'model_metadata.json').read_bytes()
    # A broken requested model must not overwrite a prior valid context.
    monkeypatch.setattr('scripts.train_disk_model.fit_on',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('injected failure')))
    with pytest.raises(RuntimeError): train(tmp_path/'sample.csv',method='rf',n_per_class=6,output_dir=out,report=report)
    assert (out/'model_metadata.json').read_bytes()==before
    make_demos(out,tmp_path/'demo')
    with (out/'test_holdout.csv').open('a') as f: f.write('\n')
    with pytest.raises(ValueError,match='artefakt'): make_demos(out,tmp_path/'demo')

def ata():
    return {'device':{'type':'sat','protocol':'ATA'},'temperature':{'current':38},'power_on_time':{'hours':1234},'ata_smart_attributes':{'table':[{'id':5,'raw':{'value':0}},{'id':9,'raw':{'value':9999999}},{'id':194,'raw':{'value':9999999}}]}}

def test_ata_missing_and_packed_fields():
    d=parse(ata())
    assert d['features']['smart_9_raw']==1234
    assert d['features']['smart_194_raw']==38
    assert 'smart_197_raw' not in d['features']
    x=model.make_features(pd.DataFrame([d['features']]))
    assert x.smart_197_raw.isna().iloc[0] and x.has_197.isna().iloc[0]
    assert list(x.columns)==model.FEATURES

@pytest.mark.parametrize('j',[{},[],None,{'device':{'type':'scsi'}},{'device':{'type':'nvme'},'nvme_smart_health_information_log':{}},{'device':{'type':'sat'},'ata_smart_attributes':{'table':[]}}])
def test_rejects_unusable(j):
    with pytest.raises(ValueError): parse(j)

@pytest.mark.parametrize('value',[-1,float('inf'),float('nan'),True,1.2,{},[]])
def test_rejects_bad_counter(value):
    j=ata(); j['ata_smart_attributes']['table'][0]['raw']['value']=value
    with pytest.raises(ValueError): parse(j)

def test_nvme_rules_missing_is_not_healthy():
    d={'kind':'nvme','temperature_c':40,'features':{'percentage_used':7}}
    assert score(d)['level']=='yellow'
    d['features'].update(critical_warning=0,media_errors=0,available_spare=100,available_spare_threshold=10)
    assert score(d)['level']=='green'
    d['features']['media_errors']=3
    assert score(d)['level']=='red'
    d['features']['media_errors']=0; d['features']['percentage_used']=255
    assert score(d)['level']=='red'
    assert any('olasılığı değildir' in x for x in score(d)['drivers'])

def test_no_labels_or_identifiers_in_features():
    f=pd.DataFrame([{'smart_5_raw':1,'failure':1,'serial_number':'X','date':'2026-04-03','lead_days':1}])
    a=model.make_features(f)
    f['failure']=0; f['serial_number']='Y'; f['date']='2000-01-01'
    pd.testing.assert_frame_equal(a,model.make_features(f))

def test_wrong_method_never_silently_falls_back(monkeypatch):
    monkeypatch.setenv('DD_DISK_MODEL','typo')
    with pytest.raises(ValueError): model.new_classifier()
    with pytest.raises(ValueError): model.predict({'kind':'nvme','features':{}})


@pytest.mark.parametrize('status', [1, 2, 4, 3, 5, 7, 129])
def test_rejects_explicit_smartctl_command_failures(status):
    payload = ata()
    payload['smartctl'] = {'exit_status': status}
    with pytest.raises(ValueError, match='okuma başarısız'):
        parse(payload)


@pytest.mark.parametrize('fields', [
    {'smart_status': {'passed': False}},
    {'smartctl': {'exit_status': 8}},
    {'smartctl': {'exit_status': 24}, 'smart_status': {'passed': True}},
])
def test_rejects_reported_failed_health_with_backup_advice(fields):
    payload = ata()
    payload.update(fields)
    with pytest.raises(ValueError, match='hemen yedekleyin'):
        parse(payload)


@pytest.mark.parametrize('fields', [
    {'smartctl': None}, {'smartctl': []},
    {'smart_status': None}, {'smart_status': []},
    *[{'smartctl': {'exit_status': value}} for value in
      (None, -1, 256, True, 0.0, 1.5, '0', float('nan'), float('inf'), [], {})],
    *[{'smart_status': {'passed': value}} for value in (None, 0, 1, 'false', [], {})],
])
def test_rejects_malformed_smartctl_status(fields):
    payload = ata()
    payload.update(fields)
    with pytest.raises(ValueError):
        parse(payload)


@pytest.mark.parametrize('fields', [
    {}, {'smartctl': {}}, {'smart_status': {}},
    {'smartctl': {'exit_status': 0}}, {'smart_status': {'passed': True}},
    {'smartctl': {'exit_status': 0}, 'smart_status': {'passed': True}},
    {'smartctl': {'exit_status': 128}},
])
def test_accepts_absent_and_clean_smartctl_status_without_changing_contract(fields):
    payload = ata()
    expected = parse(payload)
    payload.update(fields)
    assert parse(payload) == expected


def test_missing_prior_day_is_excluded_and_lead_zero_uses_failure_day(quarter, tmp_path):
    path = quarter / '2026-04-03.csv'
    day = pd.read_csv(path)
    day[day.serial_number.ne('DRIVE-000')].to_csv(path, index=False)
    early, _ = prepare(quarter, tmp_path / 'early.csv', healthy_n=24, lead_days=1)
    assert 'DRIVE-000' not in set(early.serial_number)
    assert early.failure.sum() == 15
    same_day, _ = prepare(quarter, tmp_path / 'same-day.csv', healthy_n=24, lead_days=0)
    positives = same_day[same_day.failure.eq(1)]
    assert len(positives) == 16
    assert positives.date.dt.day.eq(4).all()
    assert positives.source_failure.eq(1).all()
    assert positives.target_failure_date.eq(positives.date).all()


def test_imputation_statistics_are_fitted_only_on_training_context():
    context = pd.DataFrame({
        'serial_number': ['A', 'B', 'C', 'D'], 'failure': [0, 0, 1, 1],
        'smart_5_raw': [0, 2, 8, np.nan],
        'smart_197_raw': [0, 0, 0, 0],
    })
    clf, _ = model.fit_on(context, 'rf')
    imputer = clf.named_steps['missing']
    before = imputer.statistics_.copy()
    expected = np.median(np.log1p([0, 2, 8]))
    assert before[model.FEATURES.index('smart_5_raw')] == pytest.approx(expected)
    holdout = pd.DataFrame({'smart_5_raw': [np.nan, 1e12]})
    transformed = imputer.transform(model.make_features(holdout))
    assert transformed[0, model.FEATURES.index('smart_5_raw')] == pytest.approx(expected)
    clf.predict_proba(model.make_features(holdout))
    np.testing.assert_array_equal(imputer.statistics_, before)


def test_control_snapshots_are_not_all_earliest_dates(quarter, tmp_path):
    first, metadata = prepare(quarter, tmp_path / 'random-days.csv', healthy_n=24, healthy_days=6)
    controls = first[first.failure.eq(0)]
    assert controls.date.nunique() >= 3
    assert controls.date.value_counts().max() < 0.70 * len(controls)
    assert 'independent serial/date hash' in metadata['control_sampling']
    repeat, _ = prepare(quarter, tmp_path / 'repeat.csv', healthy_n=24, healthy_days=6)
    pd.testing.assert_frame_equal(first, repeat)


def test_snapshot_selection_ignores_directory_sort_order(quarter, tmp_path):
    original, _ = prepare(quarter, tmp_path / 'original.csv', healthy_n=24, healthy_days=6)
    reordered = tmp_path / 'reordered'
    for index, path in enumerate(sorted(quarter.glob('*.csv'))):
        target = reordered / f'{99-index:02d}' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    actual, _ = prepare(reordered, tmp_path / 'reordered.csv', healthy_n=24, healthy_days=6)
    pd.testing.assert_frame_equal(original, actual)


def test_live_nvme_export_removes_unique_identifiers():
    raw = {'device': {'type': 'nvme'}, 'model_name': 'Example NVMe',
           'serial_number': 'PRIVATE-SERIAL', 'wwn': {'id': 'PRIVATE-WWN'},
           'nvme_eui64': 'PRIVATE-EUI', 'nguid': 'PRIVATE-NGUID',
           'smartctl': {'version': [7, 5], 'exit_status': 0},
           'smart_status': {'passed': True}, 'nvme_total_capacity': 512000000000,
           'power_on_time': {'hours': 100}, 'temperature': {'current': 34},
           'nvme_smart_health_information_log': {'critical_warning': 0,
               'media_errors': 0, 'available_spare': 100, 'available_spare_threshold': 10,
               'percentage_used': 4, 'power_on_hours': 100,
               'unknown_private_field': 'PRIVATE-LOG-ID'}}
    exported = sanitized_nvme_capture(raw)
    assert 'PRIVATE-' not in json.dumps(exported)
    assert exported['serial_number'] == 'DEMO-NVME-001'
    assert exported['_provenance']['kind'] == 'live_capture'
    assert parse(exported)['features']['percentage_used'] == 4
    assert score(parse(exported))['level'] == 'green'
    raw['smart_status']['passed'] = False
    with pytest.raises(ValueError): sanitized_nvme_capture(raw)


def test_calendar_split_requires_training_target_before_cutoff():
    rows=[]
    for day in range(1, 9):
        for label in (0, 1):
            rows.append({'date': f'2026-04-{day:02d}', 'lead_days': 1,
                         'serial_number': f'{day}-{label}', 'failure': label,
                         'smart_5_raw': label})
    frame=pd.DataFrame(rows)
    context, holdout=split_data(frame, 10, test_after='2026-04-05')
    assert (pd.to_datetime(context.date) + pd.Timedelta(days=1)).le(pd.Timestamp('2026-04-05')).all()
    assert pd.to_datetime(holdout.date).gt(pd.Timestamp('2026-04-05')).all()
    assert not set(context.serial_number)&set(holdout.serial_number)
    assert not context.date.eq('2026-04-05').any()
