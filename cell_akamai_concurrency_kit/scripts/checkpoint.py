"""Local integrity checkpoint; NOT a project MMR commit or a signature.
Explicit ordered leaf bytes, domain-separated SHA256 and construction description.
"""
import hashlib,json
from pathlib import Path

def h(x):return hashlib.sha256(x).digest()
def root_from_blobs(blobs):
    layer=[h(b'\x00'+x) for x in blobs]
    if not layer:return None
    while len(layer)>1:
        layer=[h(b'\x01'+layer[i]+layer[min(i+1,len(layer)-1)]) for i in range(0,len(layer),2)]
    return layer[0].hex()
def produce(directory):
    directory=Path(directory)
    files=sorted(p for p in directory.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='LOCAL_MERKLE_BREAKPOINT.json')
    leaves=[{'path':str(p.relative_to(directory)).replace('\\','/'),'size_bytes':p.stat().st_size,
       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    payloads=[p.read_bytes() for p in files];root=root_from_blobs(payloads)
    # second pass from the actual ordered original file bytes, not stored leaf hashes
    verified=(root==root_from_blobs([(directory/x['path']).read_bytes() for x in leaves]))
    receipt={'schema':'cell-akamai.local_merkle_checkpoint.v1','ordered_leaves':leaves,
     'ordered_by':'POSIX_RELATIVE_PATH_ASC','leaf_hashing':'sha256(0x00 || exact_file_bytes)',
     'node_hashing':'sha256(0x01 || left_digest_bytes || right_digest_bytes)',
     'odd_tree':'duplicate_last_digest','local_root_sha256':root,'verification':
       'LOCAL_RECOMPUTE_PASS' if verified else 'FAILED','project_mmr_state':'NOT_COMMITTED',
     'signature_state':'NOT_SIGNED','upstream_parent_state':'EXPERIMENT_RUN_FILES',
     'notice':'Merkle integrity commitment over these files only; no trusted time, provenance truth or independent host attestation.'}
    (directory/'LOCAL_MERKLE_BREAKPOINT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return receipt
