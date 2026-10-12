from pathlib import Path
import shutil

from tools.concurrency.serve_dashboard import attestation_status

SOURCE = Path(__file__).resolve().parents[1] / 'evidence/attestation'


def test_signed_checkpoint_and_deterministic_replay_are_scoped():
    result = attestation_status(SOURCE)
    assert result['signature'] == 'VERIFIED_LOCAL_CHECKPOINT'
    assert result['deterministic_reconstruction'] == 'ESTABLISHED_FOR_FROZEN_FIXTURES'
    assert result['scientific_improvement'] == 'NOT_ESTABLISHED'
    assert result['project_mmr'] == 'NOT_INTEGRATED'


def test_changed_receipt_cannot_retain_verified_badge(tmp_path):
    shutil.copytree(SOURCE, tmp_path / 'evidence')
    (tmp_path / 'evidence/deterministic_replay.json').write_text('{}')
    result = attestation_status(tmp_path / 'evidence')
    assert result['signature'] == 'UNVERIFIED'
    assert result['deterministic_reconstruction'] == 'UNVERIFIED'


def test_invalid_signature_cannot_establish_reconstruction(tmp_path):
    shutil.copytree(SOURCE, tmp_path / 'evidence')
    (tmp_path / 'evidence/MANIFEST.json.sig').write_text('invalid')
    assert attestation_status(tmp_path / 'evidence')['signature'] == 'UNVERIFIED'
