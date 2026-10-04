"""Repair literal design references and package the reviewed draft supplement.

Semantic read-only review is recorded separately; this script verifies integrity,
not that model-written prose is automatically true.
"""
import hashlib
import json
import posixpath
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/pdlc-authoring"
SPACES = {
    "repo.payment-authorization": "space.fraud-timeout",
    "repo.identity-provisioning": "space.identity-journeys",
    "repo.ledger-reconciliation": "space.ledger-reconciliation",
    "repo.gateway-routing": "space.gateway-routing",
    "repo.fraud-batch-client": "space.fraud-batch-screening",
    "repo.shared-engineering-testing": "space.engineering-quality",
}
METADATA_REFS = {"artifact-a6faa4fd4010458f77cc", "artifact-cf9eb6d69635fba1733e", "artifact-ae542ac96deb23d875e7"}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def repair():
    data = json.loads((OUT / "pdlc-designs-draft-candidate.json").read_text())
    source = {}
    for file in (ROOT / "build/pdlc-pilot/hubs").glob("*/artifacts.jsonl"):
        for line in file.read_text().splitlines():
            r = json.loads(line)
            source[(file.parent.name, r["artifact_id"], r["version"])] = r
    repairs, count = [], 0
    for doc in data["documents"]:
        for claim in doc["audit_claims"]:
            row = source[(claim["source_id"], claim["artifact_id"], claim["version"])]
            field, text = "text", row["text"]
            if claim["quote"] not in text:
                if claim["artifact_id"] in METADATA_REFS:
                    field, text = "metadata.review_status", row["metadata"]["review_status"]
                    claim["quote"] = text
                else:
                    pattern = r"\s+".join(re.escape(t) for t in claim["quote"].split())
                    match = re.search(pattern, text)
                    if not match:
                        raise ValueError("Literal reference needs semantic repair")
                    claim["quote"] = match.group()
                repairs.append({"repo_id": doc["repo_id"], "document_key": doc["document_key"],
                                "artifact_id": claim["artifact_id"], "source_field": field})
            claim.update(source_field=field, start=text.index(claim["quote"]),
                         end=text.index(claim["quote"]) + len(claim["quote"]),
                         content_sha256=digest(row["text"].encode()))
            count += 1
        before = doc["text"]
        doc["text"] = doc["text"].replace("The code sets the R42 deadline to 800 ms.",
            "The code configures an 800 ms transport timeout; it does not establish a total request deadline.")
        if doc["repo_id"] == "repo.identity-provisioning":
            if doc["document_key"] == "hld":
                doc["text"] = doc["text"].replace(
                    "Its declared frozen/extra-forbid configuration constrains the model,",
                    "Only `FraudEvaluationRequest` declares frozen/extra-forbid configuration; "
                    "`AuthenticatedSubjectContext` declares no such configuration. "
                    "The outer settings do not establish deep immutability or nested extra-field rejection,")
            if doc["document_key"] == "evaluation-context-schema":
                doc["text"] = doc["text"].replace(
                    "The model configuration is frozen and forbids extra fields.",
                    "Only `FraudEvaluationRequest` declares `frozen=True` and `extra='forbid'`. "
                    "`AuthenticatedSubjectContext` declares no such configuration; the outer settings "
                    "do not establish deep immutability or nested extra-field rejection.")
                doc["text"] = doc["text"].replace(
                    "The strict extra-field policy narrows accepted input and the frozen model communicates immutability after construction.",
                    "The outer request's strict extra-field policy narrows its accepted input and its frozen setting "
                    "restricts assignment to that model; it does not make the nested subject deeply immutable.")
                doc["text"] = doc["text"].replace(
                    "frozen-instance behavior, extra-field rejection,",
                    "outer-request frozen-instance behavior and extra-field rejection, "
                    "nested-subject behavior under its own configuration,")
            if doc["document_key"] in ("hld", "evaluation-context-schema"):
                doc["version"] = "draft-2"
                repairs.append({"repo_id": doc["repo_id"], "document_key": doc["document_key"],
                                "repair": "RM-02: qualify outer versus nested schema configuration; draft-2"})
        for target in data["documents"]:
            if target["repo_id"] == doc["repo_id"]:
                relative = posixpath.relpath(target["path"], posixpath.dirname(doc["path"]))
                doc["text"] = doc["text"].replace("(" + target["path"] + ")", "(" + relative + ")")
        doc["related_document_paths"] = [target["path"] for target in data["documents"]
            if target["repo_id"] == doc["repo_id"] and target["document_key"] in doc["related_document_keys"]]
        if len(doc["related_document_paths"]) != len(doc["related_document_keys"]):
            raise ValueError("Missing design cross-link")
        known_paths = {d["path"] for d in data["documents"]}
        for link in re.findall(r"\]\(([^)]+)\)", doc["text"]):
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(doc["path"]), link))
            if resolved not in known_paths:
                raise ValueError("Broken design navigation link")
        if doc["text"] != before:
            repairs.append({"repo_id": doc["repo_id"], "document_key": doc["document_key"],
                            "repair": "Correct transport-timeout wording and/or relative links"})
        if any(ref not in {r["artifact_id"] for r in source.values()} for ref in doc["source_refs"]):
            raise ValueError("Unknown related evidence")
    data.update(status="references_repaired_semantic_acceptance_pending", reference_repairs=repairs,
                literal_reference_findings=[], literal_references_checked=count)
    dump("pdlc-designs-repaired-candidate.json", data)
    print(json.dumps({"documents": len(data["documents"]), "literal_references_verified": count,
                      "repair_records": len(repairs)}))


def package():
    file = OUT / "pdlc-designs-repaired-candidate.json"
    review = json.loads((OUT / "pdlc-design-semantic-review.json").read_text())
    if review["verdict"] != "pass_for_readonly_draft" or review["candidate_sha256"] != digest(file.read_bytes()):
        raise ValueError("Source-bound draft semantic review required")
    docs = json.loads(file.read_text())["documents"]
    candidate = deepcopy(json.loads((OUT / "pdlc-expanded-candidate.json").read_text()))
    hierarchy = candidate["hierarchy"]
    public = {}
    for f in (ROOT / "build/pdlc-pilot/hubs").glob("*/artifacts.jsonl"):
        for line in f.read_text().splitlines():
            row = json.loads(line)
            public[row["artifact_id"]] = row
    for i, doc in enumerate(docs):
        aid = "design." + doc["repo_id"].removeprefix("repo.") + "." + doc["document_key"]
        container_id = "collection.designs-" + doc["repo_id"].removeprefix("repo.")
        if container_id not in {n["id"] for n in hierarchy["nodes"]}:
            hierarchy["nodes"].append({"id": container_id, "kind": "collection",
                "name": doc["repo_id"].removeprefix("repo.") + " design documents",
                "parent_id": SPACES[doc["repo_id"]], "status": "synthetic_design",
                "reason": "Draft HLD/LLD navigation; does not establish runtime architecture", "evidence": []})
        if doc["kind"] == "LLD":
            module_container = container_id + "." + doc["module_key"]
            hierarchy["nodes"].append({"id": module_container, "kind": "collection", "name": doc["module_key"],
                "parent_id": container_id, "status": "synthetic_design",
                "reason": "Synthetic module navigation grouping grounded in the document; not a deployed boundary", "evidence": []})
            container_id = module_container
        refs = [public[ref] for ref in doc["source_refs"]]
        code_refs = [r for r in refs if r["metadata"]["container"]["id"] == doc["repo_id"]]
        domains = sorted({d["id"] for r in code_refs for d in r["metadata"].get("domains", [])})
        services = sorted({s["id"] for r in code_refs for s in r["metadata"].get("services", [])})
        artifact = {k: doc[k] for k in ("title", "path", "version", "review_status", "text", "source_refs", "module_key", "related_document_paths")}
        artifact.update(artifact_id=aid, hub="dochub", document_kind=doc["kind"],
            chronology="Synthetic draft authoring; no historical approval, deployment or test execution implied",
            source_file=file.name, source_sha256=digest(file.read_bytes()), artifact_index=i)
        candidate["artifacts"].append(artifact)
        hierarchy["mappings"].append({"artifact_id": aid, "hub": "dochub", "container_id": container_id,
            "logical_path": doc["path"], "domain_ids": domains, "service_ids": services,
            "related_repo_ids": [doc["repo_id"]], "team_roles": [], "status": "synthetic_design",
            "reason": "Reviewed synthetic design draft linked to packet-bound repo and source evidence",
            "evidence": [], "unresolved": ["Design remains draft/unapproved; module is navigation only"],
            "source": {"source_file": file.name, "source_sha256": digest(file.read_bytes()),
                "artifact_index": i, "version": doc["version"], "metadata": {"document_kind": doc["kind"]},
                "audited_content_sha256": digest(doc["text"].encode())}})
    candidate["supplement"]["expected_artifacts"] = len(candidate["artifacts"])
    candidate["design_supplement"] = {"status": "source_semantic_review_passed", "documents": len(docs),
        "reviewer": review["reviewer"], "review_sha256": digest((OUT / "pdlc-design-semantic-review.json").read_bytes()),
        "design_candidate_sha256": digest(file.read_bytes())}
    dump("pdlc-design-expanded-candidate.json", candidate)
    print(json.dumps({"candidate_records": len(candidate["artifacts"]), "new_design_documents": len(docs)}))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("repair", "package"))
    a = p.parse_args()
    repair() if a.stage == "repair" else package()
