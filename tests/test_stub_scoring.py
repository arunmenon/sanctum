from sanctum_contracts import EvidenceResponse, Receipt, RetrieveRequest
from sanctum_eval.metrics import score_case
from sanctum_stub.stub import StubSUT

from .conftest import CASES


def test_stub_advertises_partial_verify():
    caps = StubSUT().capabilities()
    assert caps.modes["verify"].value == "partial"
    assert caps.features["writes"].value == "unsupported"


def test_independent_stub_is_scoreable(case):
    """M0 exit: an independent stub produces responses the evaluator can fully score."""
    sut = StubSUT()
    for cid in CASES:
        gold, _, _, trace = case(cid)
        public = RetrieveRequest.model_validate(gold.request.model_dump())  # only public fields
        resp, receipt = sut.retrieve(public)
        s = score_case(gold, resp, receipt, trace)
        assert s.gates_failed == [], (cid, s.gates_failed)
        assert s.safe_grounded_success, (cid, s)


def test_expected_metric_values(case):
    gold, r, rc, t = case("m0-001")
    s = score_case(gold, EvidenceResponse.model_validate(r), Receipt.model_validate(rc), t)
    assert s.recall == 1.0 and s.conflict_witnesses == 1.0 and s.sources_attempted == 2
    gold, r, rc, t = case("m0-003")
    s = score_case(gold, EvidenceResponse.model_validate(r), Receipt.model_validate(rc), t)
    assert s.recall == 0.5 and s.harmful_omission is True and s.silent_omission is False
    assert s.safe_grounded_success  # unobtainable support reported honestly
