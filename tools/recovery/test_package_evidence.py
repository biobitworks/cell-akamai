import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

spec = importlib.util.spec_from_file_location('package_evidence', Path(__file__).with_name('package_evidence.py'))
pkg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)


def test_private_response_removed_but_usage_kept():
    value = pkg.sanitize({'request': {'messages': [{'content': 'private prompt'}]},
                          'response': {'text': 'private reply'}, 'completion_tokens': 17,
                          'nested': {'api_key': 'private key'}})
    body = json.dumps(value)
    assert 'private prompt' not in body and 'private reply' not in body and 'private key' not in body
    assert value['completion_tokens'] == 17


def test_reopen_manifest_and_detect_changed_member(tmp_path):
    path = tmp_path / 'valid.zip'
    receipt = pkg.write_zip(path, {'summary.json': b'{"failed":8}\n'})
    assert receipt['state'] == 'REOPEN_VERIFIED' and receipt['member_hashes_verified'] == 1
    with pytest.raises(AssertionError):
        pkg.write_zip(path, {})


@pytest.mark.parametrize('member', ['../escape', '/absolute'])
def test_unsafe_zip_rejected(tmp_path, member):
    path = tmp_path / 'bad.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(member, 'unsafe')
    with pytest.raises(AssertionError):
        pkg.verify_archive(path)


def test_manifest_layouts():
    digest = 'a' * 64
    assert pkg.declared_hashes({'files': {'file': digest}}) == {'file': digest}
    assert pkg.declared_hashes({'source_snapshot_file_checks': [{'path': 'file', 'sha256': digest}]}) == {'file': digest}


def test_symlink_zip_rejected(tmp_path):
    path = tmp_path / 'link.zip'
    info = zipfile.ZipInfo('link')
    info.create_system = 3
    info.external_attr = 0o120777 << 16
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(info, '/private')
    with pytest.raises(AssertionError):
        pkg.verify_archive(path)
