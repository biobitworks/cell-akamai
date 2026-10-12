from cell_akamai.dashboard import write_dashboard, load_snapshot


def test_empty_dashboard_does_not_invent_experiments(tmp_path):
    empty=load_snapshot(tmp_path/"runs")
    assert empty["runs"]==[] and empty["lane_b"]==[]
    assert empty["anticube_state"]=="NOT_COMPUTED"
    assert empty["delta_g_star_state"]=="NOT_COMPUTED"
    html=write_dashboard(tmp_path/"runs", output=tmp_path/"dashboard.html").read_text()
    assert 'NOT_TESTED' in html
    assert 'NOT_COMPUTED' in html
    assert 'MMR: NOT_COMMITTED' in html
