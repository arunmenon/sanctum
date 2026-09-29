"""Test-only SUTs: a fan-out probe that calls every hub once and answers with no evidence,
and a recorder of what a SUT receives (answers with the stub's canned m0 response)."""
from sanctum_contracts import CONTRACT_REVISION, EvidenceResponse, Receipt
from sanctum_stub.stub import StubSUT

# One cheap, argument-light tool per hub.
PROBE_TOOLS = {
    "codehub": ("list_repos", {}),
    "skillhub": ("list_tree", {}),
    "dochub": ("list_spaces", {}),
    "memoryhub": ("search_sessions", {"query": "retry"}),
    "incidenthub": ("search_incidents", {"query": "retry"}),
}


class FanOutProbeSUT:
    def __init__(self):
        self.payloads: dict[str, dict] = {}

    async def retrieve(self, request, context):
        for hub_id in context.gateway.hub_ids:
            tool, arguments = PROBE_TOOLS[hub_id]
            self.payloads[hub_id] = await context.gateway.call(hub_id, tool, arguments)
        return empty_answer(request, self.payloads)


def empty_answer(request, payloads: dict[str, dict]):
    """A contract-valid response carrying no evidence, reporting the hubs it called."""
    receipt_id = f"rc-probe-{request.request_id}"
    response = EvidenceResponse.model_validate({
        "request_id": request.request_id, "receipt_id": receipt_id, "memory_release_id": "none",
        "effective_scope_ref": "probe", "replay_level": "recompute_on_candidates",
        "interpretations": [], "evidence": [],
        "sources": [{"source_id": hub_id, "status": "called", "reasons": ["routing_selected"]}
                    for hub_id in payloads],
        "evidence_status": "insufficient", "reasons": [],
        "budget": {"requested": request.budget_tokens, "used": 0, "tokenizer_id": "cl100k_base"},
    })
    receipt = Receipt.model_validate({
        "receipt_id": receipt_id, "request_id": request.request_id, "config_id": "probe",
        "contract_revision": CONTRACT_REVISION, "memory_release_id": "none",
        "resolutions": [], "activations": [],
        "calls": [{"source_id": hub_id, "tool": PROBE_TOOLS[hub_id][0],
                   "status": "ok" if "error" not in payload else "error", "started_ms": 0, "ended_ms": 0}
                  for hub_id, payload in payloads.items()],
    })
    return response, receipt


class RecordingSUT:
    def __init__(self):
        self.requests: list[dict] = []
        self.contexts: list = []

    async def retrieve(self, request, context):
        self.requests.append(request.model_dump())
        self.contexts.append(context)
        return StubSUT().retrieve(request)
