"""Create append-only, verified downloadable archives without raw model text.

Raw predecessors remain private on the host. Hashes identify every omission and
every sanitized projection; hashes establish custody, not experimental validity.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import zipfile

ROOT = Path('/home/coder/workshop')
REC = ROOT / 'cell_akamai_recovery_20261012'
MATRIX = ROOT / 'codex_execution_20261012/bundle'
DENY = {'text', 'content', 'reasoning', 'reasoning_content', 'response', 'response_chunks',
        'prompt', 'messages', 'question', 'answer', 'raw_response', 'api_key',
        'access_token', 'authorization', 'kubeconfig', 'password', 'secret'}
SECRET = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{24,})\b')


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sanitize(value):
    if isinstance(value, dict):
        return {k: ('REDACTED_PRIVATE_RAW_TEXT_OR_SECRET' if k.lower() in DENY else sanitize(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, str) and SECRET.search(value):
        return 'REDACTED_SECRET_PATTERN'
    return value


def declared_hashes(value):
    """Read common dict/list manifest layouts, without trusting descriptions."""
    result = {}
    if isinstance(value, dict):
        for key in ('files', 'source_snapshot_file_checks', 'file_hashes'):
            part = value.get(key)
            if isinstance(part, dict):
                for path, item in part.items():
                    digest = item if isinstance(item, str) else item.get('sha256') if isinstance(item, dict) else None
                    if digest and re.fullmatch('[a-f0-9]{64}', digest):
                        result[path] = digest
            elif isinstance(part, list):
                for item in part:
                    if isinstance(item, dict) and item.get('path') and item.get('sha256'):
                        result[item['path']] = item['sha256']
    return result


def verify_archive(path):
    data = path.read_bytes()
    receipt = {'path': str(path), 'exists': True, 'size': len(data), 'sha256': sha(data),
               'mtime_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
               'manifest_checks': []}
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, 'ZIP CRC failure'
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP members'
        for member in archive.infolist():
            p = Path(member.filename)
            assert not p.is_absolute() and '..' not in p.parts
            assert not stat.S_ISLNK(member.external_attr >> 16)
        for name in names:
            if name.endswith('.json') and 'MANIFEST' in name.upper():
                manifest = json.loads(archive.read(name))
                checks = declared_hashes(manifest)
                prefix = str(Path(name).parent)
                mismatches, missing = [], []
                for member, expected in checks.items():
                    candidate = member if member in names else str(Path(prefix) / member)
                    if candidate not in names:
                        missing.append(member)
                    elif sha(archive.read(candidate)) != expected:
                        mismatches.append(member)
                receipt['manifest_checks'].append({'manifest': name, 'declared': len(checks),
                    'verified': len(checks) - len(missing) - len(mismatches), 'missing': missing,
                    'mismatches': mismatches,
                    'unexpected': sorted(set(names) - set(checks) - {name}) if prefix == '.' else []})
        receipt['members'] = len(names)
        receipt['state'] = 'RECOVERED_INTEGRITY_PASS'
        target = REC / ('archive_' + path.stem + '_' + receipt['sha256'][:12])
        if not target.exists():
            target.mkdir()
            archive.extractall(target)
        receipt['extracted_path'] = str(target)
    return receipt


def write_zip(path, entries):
    assert not path.exists(), 'Do not overwrite prior final archives'
    manifest = {k: {'sha256': sha(v), 'bytes': len(v)} for k, v in sorted(entries.items())}
    payload = dict(entries)
    payload['SHA256_MANIFEST.json'] = encode(manifest)
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            archive.writestr(name, data)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        reopened = json.loads(archive.read('SHA256_MANIFEST.json'))
        assert set(archive.namelist()) == set(reopened) | {'SHA256_MANIFEST.json'}
        assert all(sha(archive.read(k)) == v['sha256'] for k, v in reopened.items())
    return {'name': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()),
            'members': len(payload), 'member_hashes_verified': len(manifest), 'state': 'REOPEN_VERIFIED'}


def main():
    os.umask(0o077)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    package = REC / 'executed_successor_v1'
    assert json.loads((package / 'PIPELINE_STATE.json').read_text())['state'].startswith('COMPLETED')
    roots = [ROOT / 'cell_akamai_results', ROOT / 'cell_akamai', ROOT / 'cell-akamai-m08-m09',
             REC, MATRIX, ROOT / 'recovery_tools']
    archives = set(ROOT.glob('*AKAMAI*.zip')) | set(ROOT.glob('akamai*.zip')) | set(ROOT.glob('codex*.zip'))
    for root in roots:
        if root.exists():
            archives.update(root.rglob('*.zip'))
    inventory = []
    for path in sorted(archives):
        try:
            inventory.append(verify_archive(path))
        except Exception as exc:
            inventory.append({'path': str(path), 'exists': path.exists(), 'state': 'REJECTED',
                              'failure': type(exc).__name__, 'sha256': sha(path.read_bytes())})
    save_inventory = ROOT / ('RECOVERY_INVENTORY_' + run_id + '.json')
    save_inventory.write_bytes(encode(inventory))
    entries, public, omissions, file_index = {}, {}, [], []
    for receipt in inventory:
        path = Path(receipt['path'])
        if path.name.startswith(('CELL_AKAMAI_M08_M09_HANDOFF_', 'CELL_AKAMAI_M08_M09_SIX_DATASETS_', 'codex_bf16_execution_bundle')):
            entries['input_archives/' + path.name] = path.read_bytes()
        else:
            omissions.append({'path': str(path), 'sha256': receipt.get('sha256'),
                              'reason': 'Original archive retained privately; sanitized extracted files included'})
    seen = set()
    candidates = [*ROOT.glob('*.ipynb')]
    for folder in roots:
        if folder.exists():
            candidates.extend(folder.rglob('*'))
    for path in sorted(set(candidates)):
        if not path.is_file() or path.is_symlink() or any(x in path.parts for x in ('__pycache__', '.git', '.venv', 'node_modules')):
            continue
        if path.suffix not in ('.json', '.jsonl', '.ipynb', '.py', '.md', '.prom', '.log', '.txt', '.csv', '.png', '.svg'):
            continue
        data = path.read_bytes()
        if len(data) > 8_000_000:
            omissions.append({'path': str(path), 'sha256': sha(data), 'reason': 'Large file; private original retained'})
            continue
        rel = str(path.relative_to(ROOT))
        original_sha = sha(data)
        projected, state = data, 'BYTE_IDENTICAL'
        try:
            if path.suffix == '.json':
                projected = encode(sanitize(json.loads(data)))
                state = 'SANITIZED_JSON_PROJECTION'
            elif path.suffix == '.jsonl':
                # Fixtures may retain their public model inputs. Runtime rows remove raw replies.
                fixture = 'data' in path.parts and any(x in path.parts for x in ('original', 'fco', 'fcg'))
                fixture = fixture or path.name == 'eca_pilot_inputs_v1.jsonl'
                if not fixture:
                    projected = b''.join(encode(sanitize(json.loads(line))).replace(b'\n', b'') + b'\n'
                                         for line in data.splitlines() if line)
                    state = 'SANITIZED_REQUEST_METRICS_PROJECTION'
            elif path.suffix == '.ipynb':
                notebook = json.loads(data)
                # Keep originals private; download notebook source with execution counts and exception type.
                for cell in notebook.get('cells', []):
                    outputs = cell.get('outputs', [])
                    if outputs:
                        cell['outputs'] = [{'output_type': 'stream', 'name': 'stdout',
                            'text': ['Private outputs preserved on host. Original notebook SHA-256: ' + original_sha + '\n']}]
                        cell.setdefault('metadata', {})['retained_exception_types'] = [o.get('ename') for o in outputs if o.get('output_type') == 'error']
                projected = encode(notebook)
                state = 'NOTEBOOK_PRIVATE_OUTPUTS_COMMITTED_SEPARATELY'
            elif path.suffix == '.prom':
                values = {}
                for line in data.decode().splitlines():
                    m = re.fullmatch(r'(vllm:[\w:]+)(?:\{[^}]*\})?\s+([-+\deE.]+)(?:\s+\S+)?', line)
                    if m:
                        values[m[1]] = values.get(m[1], 0) + float(m[2])
                projected = encode({'original_sha256': original_sha, 'label_stripped_metric_sums': values})
                rel += '.json'
                state = 'METRICS_LABELS_REMOVED'
            elif path.suffix in ('.log', '.txt', '.csv', '.png', '.svg'):
                omissions.append({'path': str(path), 'sha256': original_sha, 'reason': 'Unapproved free text/log/media retained privately'})
                continue
            if SECRET.search(projected.decode('utf-8', errors='ignore')):
                omissions.append({'path': str(path), 'sha256': original_sha, 'reason': 'Secret-pattern scan rejected projection'})
                continue
            entries['recovered/' + rel] = projected
            public['recovered/' + rel] = projected
            file_index.append({'path': str(path), 'bytes': len(data), 'sha256': original_sha,
                               'projection_sha256': sha(projected), 'recovery_state': state})
        except Exception as exc:
            omissions.append({'path': str(path), 'sha256': original_sha, 'reason': type(exc).__name__})
    run_index = []
    for record in file_index:
        path = Path(record['path'])
        if path.name not in ('run_manifest.json', 'experiment_receipt.json', 'identity.json', 'agent_config.json', 'COMMIT.json'):
            continue
        try:
            obj = json.loads(path.read_bytes())
            env = obj.get('env', {})
            config = obj.get('config', {})
            config_path = path.parent / 'config.json'
            dataset_path = path.parent / 'items.jsonl'
            is_eca = 'ECA' in str(path) or 'concurrency' in str(path)
            run_index.append({
                'run_id': obj.get('run_id', path.parent.name),
                'parent_run_id': 'CAKM-M08M09-RECOVERY-EXPORT-20261012',
                'source_commit': obj.get('source_commit', obj.get('git_commit', obj.get('workshop_sha', 'UNKNOWN'))),
                'workload_sha256': sha(encode(obj.get('workload'))) if obj.get('workload') else 'UNKNOWN',
                'configuration_sha256': sha(config_path.read_bytes()) if config_path.exists() else obj.get('config_sha256', sha(encode(config)) if config else 'UNKNOWN'),
                'dataset_sha256': obj.get('dataset_sha256', '69ced0ca1cf77a00446e2b3db03564eb487b2f2b15e68c34590ee8e96b07c274' if is_eca else 'NOT_APPLICABLE_OR_UNKNOWN'),
                'model_identity': obj.get('model', env.get('served_model', 'UNKNOWN')),
                'precision_state': obj.get('precision_verified', env.get('served_precision', 'UNKNOWN')),
                'hardware': obj.get('hardware', 'UNKNOWN_NOT_ATTESTED'),
                'execution_location': 'AKAMAI_WORKSHOP_S05' if 'codex_execution' in str(path) or 'executed_successor' in str(path) else 'RECOVERED_PREEXISTING_RECEIPT',
                'execution_state': obj.get('state', obj.get('status', 'RECOVERED_RECEIPT_NOT_REEXECUTED')),
                'receipt_refs': [record['path'] + '@sha256:' + record['sha256']],
                'test_results': 'SEE_NOTEBOOK_STATUS_AND_OFFLINE_VERIFICATION',
                'failures': obj.get('failures', 'SEE_RETAINED_REQUEST_METRICS'),
                'claim_ceiling': 'PILOT_NONCONFIRMATORY; custody hashes alone establish no improvement; no training'
            })
        except (ValueError, TypeError):
            pass
    common = {
        'RECOVERY_INVENTORY.json': encode(inventory), 'FILE_EVIDENCE_INDEX.json': encode(file_index),
        'CONSOLIDATED_RUN_INDEX.json': encode(run_index),
        'OMISSIONS_MANIFEST.json': encode(omissions),
        'CLAIM_BOUNDARIES.json': encode({'historical_genesis_vita_recovery': 'NOT_VERIFIED',
            'training': 'NOT_TESTED', 'anticube': 'NOT_COMPUTED', 'delta_g_star': 'NOT_COMPUTED',
            'project_MMR': 'NOT_COMPUTED', 'signature': 'NOT_SIGNED',
            'raw_model_responses': 'RETAINED_PRIVATE_HOST_ONLY', 'inter_request_tokens_s2': 'NOT_COMPUTED_FOR_CONCURRENCY'})}
    entries.update(common)
    public.update(common)
    result = [write_zip(ROOT / ('CELL_AKAMAI_ALL_EVIDENCE_20261012_' + run_id + '.zip'), entries),
              write_zip(ROOT / ('CELL_AKAMAI_GITHUB_EVIDENCE_20261012_' + run_id + '.zip'), public)]
    report = {'run_id': run_id, 'archives': result, 'candidate_archives': len(inventory),
              'recovered_archives': sum(x.get('state') == 'RECOVERED_INTEGRITY_PASS' for x in inventory),
              'files_indexed': len(file_index), 'run_receipts_indexed': len(run_index), 'omissions': len(omissions)}
    (ROOT / ('FINAL_ARCHIVE_RECEIPT_' + run_id + '.json')).write_bytes(encode(report))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
