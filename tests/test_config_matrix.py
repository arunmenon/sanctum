from tools.config_diff import check_comparison, diff, load


def test_all_arms_declare_same_switches():
    m = load()
    keys = {tuple(sorted(v)) for v in m["arms"].values()}
    assert len(keys) == 1


def test_primary_comparisons_change_only_allowed_switches():
    m = load()
    for name in m["comparisons"]:
        d, extra = check_comparison(m, name)
        assert d, f"{name} compares identical arms"
        assert not extra, f"{name} differs in unexpected switches {extra}"


def test_semantics_ablation_holds_storage_fixed():
    m = load()
    assert set(diff(m, "C4a-equivalent", "C4a-label-only")) == {"resolution"}


def test_fair_fanout_shares_assembly():
    m = load()
    assert m["arms"]["C1-fair"]["assembly"] == m["arms"]["C2"]["assembly"]
    assert m["comparisons"]["descriptive_only"]["causal"] is False
