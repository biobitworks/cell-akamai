from cell_akamai.contract import validate_lane_b_result
from cell_akamai.dashboard import load_snapshot
import json


def test_lane_b_fail_closed(tmp_path):
    valid={"schema_version":"cell_akamai.lane_b_result.v1","experiment_id":"EXP-01",
           "arm":"B0_FIXED","metric":"accuracy","unit":"fraction","value":.5,
           "status":"OBSERVED","evidence_ref":"sha256:abc","evaluation_split":"heldout",
           "source_class":"OBSERVED"}
    assert validate_lane_b_result(valid) == []
    bad=dict(valid, status="NOT_COMPUTED",value=.5)
    assert "NON_OBSERVED_VALUE_MUST_BE_NULL" in validate_lane_b_result(bad)
    file=tmp_path/"lane_b.jsonl"
    file.write_text(json.dumps(valid)+'\n'+json.dumps(bad)+'\n')
    snapshot=load_snapshot(tmp_path/"empty",file)
    assert len(snapshot['lane_b'])==1 and len(snapshot['lane_b_rejections'])==1
