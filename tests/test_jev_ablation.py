"""A calibrated skip recommendation is distinct from an observed hub skip."""
import json

from tools.finish_active_jev_ablation import recommendations


def test_applied_and_guarded_recommendations_stay_separate(tmp_path):
    folder=tmp_path/'attempts'/'one';folder.mkdir(parents=True)
    def call(shadow,skip,called):
        return {'router_receipt':{'decisions':[{'value':{'source':'codehub','shadow':shadow,'call':not skip}}]},
                'backend_trace':{'calls':[{'source_id':source} for source in called]}}
    result={'arm':'sanctum','mcp_calls':[call(False,True,['codehub']),call(False,True,['dochub']),call(True,False,['codehub'])]}
    (folder/'result.json').write_text(json.dumps(result))
    counts=recommendations(tmp_path)
    assert counts['skip_recommendations']==2
    assert counts['guarded_or_other_call']==1
    assert counts['skip_with_no_observed_hub_call']==1
    assert counts['active']==2 and counts['shadow']==1
    assert counts['hub_calls']==3
