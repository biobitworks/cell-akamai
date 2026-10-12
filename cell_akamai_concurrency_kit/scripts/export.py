"""Portable verified ZIP with byte-level SHA-256 manifest, without claiming MMR signing."""
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path

def export_run(run_dir, output):
    run=Path(run_dir);output=Path(output)
    files=sorted(p for p in run.rglob('*') if p.is_file() and not p.is_symlink())
    if not files:raise ValueError('No experiment evidence found')
    manifest={'schema':'cell-akamai.export.v1','source':'OPERATOR_EXPORTED',
      'verification':'ZIP_READBACK_PASS_NOT_INDEPENDENT_SOURCE_ATTESTATION',
      'mmr':'NOT_COMMITTED','signature':'NOT_SIGNED','files':[]}
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            name=p.relative_to(run).as_posix();data=p.read_bytes()
            info=zipfile.ZipInfo('runs/'+name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data);manifest['files'].append({'path':'runs/'+name,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)})
        data=json.dumps(manifest,indent=2,sort_keys=True).encode()
        info=zipfile.ZipInfo('EXPORT_MANIFEST.json',(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:raise RuntimeError('CRC invalid')
        for f in manifest['files']:
            if hashlib.sha256(z.read(f['path'])).hexdigest()!=f['sha256']:raise RuntimeError('Hash mismatch')
    return {'zip':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(files)}
