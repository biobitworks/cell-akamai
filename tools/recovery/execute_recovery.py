"""Authorized hosted notebook sequence. Original archives remain untouched.

Run in the authenticated Akamai workspace, after uploading the reviewed script.
No credentials or raw answers are printed. Failed notebooks remain in evidence.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import nbformat
from nbclient import NotebookClient

ROOT = Path('/home/coder/workshop')
RECOVERY = ROOT / 'cell_akamai_recovery_20261012'
SOURCE = next(RECOVERY.glob('CELL_AKAMAI_M08_M09_SIX_DATASETS*'))
PACKAGE = RECOVERY / 'executed_successor_v1'
MATRIX = ROOT / 'codex_execution_20261012/bundle'
os.umask(0o077)
os.environ['NAMESPACE'] = 'workshop-s05'
os.environ['WORKSHOP_REPO'] = str(MATRIX / 'workshop')


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def idle():
    import requests
    for _ in range(3):
        text = requests.get('http://vllm:8000/metrics', timeout=20).text
        values = [float(s.rsplit(' ', 1)[1]) for s in text.splitlines()
                  if s.startswith(('vllm:num_requests_running{', 'vllm:num_requests_waiting{'))]
        assert len(values) >= 2 and not any(values), 'Shared inference server is busy'
        time.sleep(1)


def execute(name, modify=None):
    source = SOURCE / 'notebooks' / (name + '.ipynb')
    notebook = nbformat.read(source, as_version=4)
    if modify:
        modify(notebook)
    dest = PACKAGE / 'notebooks' / (name + '_EXECUTED.ipynb')
    assert not dest.exists(), 'Append-only notebook output already exists'
    errors = []
    try:
        NotebookClient(notebook, timeout=1800, kernel_name='python3', allow_errors=True,
                       resources={'metadata': {'path': str(dest.parent)}}).execute()
    except Exception as exc:
        errors.append({'type': type(exc).__name__})
    finally:
        nbformat.write(notebook, dest)
    for cell in notebook.cells:
        errors.extend({'type': o.get('ename'), 'message': o.get('evalue')}
                      for o in cell.get('outputs', []) if o.output_type == 'error')
    receipt = {'notebook': dest.name, 'original_sha256': sha(source),
               'executed_sha256': sha(dest), 'state': 'FAILED' if errors else 'EXECUTED',
               'errors': errors, 'serving_policy_authorized': name.startswith('80_'),
               'raw_responses_printed': False}
    save(PACKAGE / (name + '_STATUS.json'), receipt)
    print(name, receipt['state'], flush=True)
    return receipt


def offline(notebook):
    for cell in notebook.cells:
        if cell.cell_type == 'code' and 'import pandas as pd' in cell.source:
            cell.source = cell.source.replace('import pandas as pd', '# Optional pandas display removed; same computed rows')
            cell.source = cell.source.replace('display(pd.DataFrame(rows))', 'print(json.dumps(rows,indent=2))')


def tune(notebook):
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.source = cell.source.replace('AUTHORIZE_ONE_FLAG_ROLLOUT=False', 'AUTHORIZE_ONE_FLAG_ROLLOUT=True')
    notebook.cells.insert(1, nbformat.v4.new_markdown_cell(
        'Operator authorized tuning in this session. Exactly one guarded serving-policy change: '
        '--max-num-seqs 32 → 64. Original model, image, workload and other flags fixed. '
        'Starts only after full BF16 matrix finishes and idle checks pass. No automatic rollback.'))


def agents(notebook):
    for cell in notebook.cells:
        if cell.cell_type != 'code':
            continue
        cell.source = cell.source.replace(
            "print(json.dumps(cak.read_json(M09_AGENT/'agent_results.json'),indent=2)[:15000])",
            "print('Private agent records retained; aggregate export only')")
        if 'M09_ECA=cak.run_eca' in cell.source:
            cell.source = cell.source.replace(
                'M09_ECA=cak.run_eca(ENV,n_items=N_ITEMS,max_tokens=128,call_cap=3,token_cap=384)',
                "import contextlib\nwith (PACKAGE/'private_eca_progress.log').open('w') as _log, contextlib.redirect_stdout(_log):\n    M09_ECA=cak.run_eca(ENV,n_items=N_ITEMS,max_tokens=128,call_cap=3,token_cap=384)")


def paired(notebook):
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.source = cell.source.replace('RUN_AKAMAI_GPU=False', 'RUN_AKAMAI_GPU=True')


def export(notebook):
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.source = cell.source.replace('INCLUDE_RAW=True', 'INCLUDE_RAW=False')


def main():
    manifest = json.loads((SOURCE / 'PACKAGE_MANIFEST.json').read_text())
    assert len(manifest['files']) == 21
    assert all(sha(SOURCE / k) == v for k, v in manifest['files'].items())
    shutil.copytree(SOURCE, PACKAGE, ignore=shutil.ignore_patterns('*EXECUTED*', '*.pyc', '__pycache__', 'runs'))
    helper = PACKAGE / 'cell_akamai_handoff.py'
    source = helper.read_text()
    # Missing gauges are unknown, never zero. Only observed finite samples enter maxima.
    source = source.replace("max([z.get('vllm:num_requests_running') or 0 for z in samples],default=None)",
                            "max([z['vllm:num_requests_running'] for z in samples if z.get('vllm:num_requests_running') is not None],default=None)")
    source = source.replace("max([z.get('vllm:num_requests_waiting') or 0 for z in samples],default=None)",
                            "max([z['vllm:num_requests_waiting'] for z in samples if z.get('vllm:num_requests_waiting') is not None],default=None)")
    helper.write_text(source)
    save(PACKAGE / 'EXECUTION_ADAPTATIONS.json', {
        'parent_archive_sha256': 'cc319eccd4e27e506443e10a694412906c9c6d79fc9c73f6fe1aea7d2d0cbd48',
        'helper_original_sha256': sha(SOURCE / helper.name), 'helper_execution_sha256': sha(helper),
        'changes': ['optional pandas display replaced with JSON', 'explicit authorized max-num-seqs rollout',
                    'raw ECA progress redirected to private log', 'raw export disabled', 'missing gauges remain null'],
        'historical_recovery': 'NOT_VERIFIED', 'training': 'NOT_TESTED', 'MMR': 'NOT_COMPUTED'})
    execute('83_six_dataset_offline_verify', offline)
    save(PACKAGE / 'PIPELINE_STATE.json', {'state': 'WAITING_FOR_BF16_MATRIX'})
    while not (MATRIX / 'BF16_FULL_MATRIX_EXECUTED.ipynb').exists():
        time.sleep(10)
    status = json.loads((MATRIX / 'runs_fullmatrix/pilot_status.json').read_text())
    assert status['status'] == 'COMPLETED', 'Full matrix execution failed before completion'
    idle()
    save(PACKAGE / 'PIPELINE_STATE.json', {'state': 'MODULE08_RUNNING'})
    execute('80_m08_tune_before_after', tune)
    idle()
    save(PACKAGE / 'PIPELINE_STATE.json', {'state': 'MODULE09_RUNNING'})
    execute('81_m09_agent_and_daisy', agents)
    idle()
    execute('84_six_dataset_akamai_paired', paired)
    execute('82_verify_and_export', export)
    save(PACKAGE / 'PIPELINE_STATE.json', {'state': 'COMPLETED_WITH_RETAINED_EXCEPTIONS'})


if __name__ == '__main__':
    main()
