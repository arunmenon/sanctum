"""Round 3 state records for the System One broker (prompt review §2; state layout "r3-state-v2").

Every field is built by the broker from the hub row it read itself:

- provenance: source_id, artifact_id, version, environment (from the row);
- subject, attribute, assertion_role: deterministic, source-supported extraction only, else null.
  subject is a skill's front-matter `name:`, else the first markdown heading, else the repo or
  space the row lives in; attribute is the first assigned name (`NAME = ...`, `key: value`) on a
  selected assertion line; assertion_role follows the hub's kind of source. Every non-null value
  occurs verbatim in the artifact's text or location, so no evaluator or world-private
  vocabulary can enter;
- excerpt, excerpt_spans: the excerpt policy below, within the retrieved span only.

Excerpt policy: within [start, end), select lines containing a query term or an assertion pattern
(a name assigned a value), add the adjacent lines, and keep every qualifier line (environment,
release, version, branch, heading) of the span whenever any line is selected. Lines keep their
original order and exact text, joined by newlines; their artifact offsets are recorded. The
excerpt is capped at MAX_EXCERPT_CHARS by dropping whole lines from the end. With no selected
line, a bounded prefix of the span is kept.

State layout "r3-state-v1" (the earlier {source_id, version, environment, text} slice) stays
available for the ablation baseline.
"""
from __future__ import annotations

import re
from typing import Any, Optional

STATE_V1 = "r3-state-v1"
STATE_V2 = "r3-state-v2"
STATE_V2_COMPACT = "r3-state-v2-compact"   # small-context providers (Laya): same fields, qualifiers first
STATE_LAYOUTS = (STATE_V1, STATE_V2, STATE_V2_COMPACT)
MAX_EXCERPT_CHARS = 1200
PREFIX_CHARS = 400
COMPACT_EXCERPT_CHARS = 350

ROLE_BY_SOURCE = {"codehub": "implemented_behavior", "skillhub": "procedure", "dochub": "reference",
                  "memoryhub": "session_note", "incidenthub": "incident"}
ASSIGNMENT = re.compile(r"(?:^|[\s,{(])([A-Za-z_][A-Za-z0-9_.-]{1,60})\s*(?:=|:)\s*[\"']?[-\w.]")
QUALIFIER = re.compile(r"(?i)\b(environment|env|prod|production|staging|experiment|release|version|branch)\b"
                       r"|\bR\d{2,}\b|^\s*#")
STOPWORDS = {"the", "and", "for", "what", "how", "does", "did", "was", "are", "with", "that", "this", "when",
             "which", "who", "many", "much", "use", "uses", "its", "from", "into", "about", "there"}


def query_terms(query: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", query.lower()) if len(word) >= 3 and word not in STOPWORDS}


def _lines(text: str, start: int, end: int) -> list[tuple[int, int, str]]:
    """(artifact start, artifact end, line text) for each line of text[start:end]."""
    out, cursor = [], start
    for piece in text[start:end].split("\n"):
        out.append((cursor, cursor + len(piece), piece))
        cursor += len(piece) + 1
    return out


def _is_assertion(line: str) -> bool:
    return bool(ASSIGNMENT.search(line)) and bool(re.search(r"\d", line))


def excerpt_of(text: str, start: int, end: int, query: str, max_chars: int = MAX_EXCERPT_CHARS,
               prefix_chars: int = PREFIX_CHARS, qualifiers_first: bool = False) -> tuple[str, list[dict[str, int]], list[str]]:
    """(excerpt, spans, selected lines) per the module's excerpt policy. With `qualifiers_first`
    (compact layout) qualifier lines are admitted before other selected lines, so a tight cap never
    drops a value's environment or release; output stays in original order."""
    lines = _lines(text, start, end)
    terms = query_terms(query)
    chosen: set[int] = set()
    for index, (_, _, line) in enumerate(lines):
        words = set(re.findall(r"[a-z0-9]+", line.lower()))
        if (terms & words) and line.strip() or _is_assertion(line):
            chosen |= {index - 1, index, index + 1}
    chosen = {i for i in chosen if 0 <= i < len(lines) and lines[i][2].strip()}
    if chosen:
        qualifiers = {i for i, (_, _, line) in enumerate(lines) if line.strip() and QUALIFIER.search(line)}
        chosen |= qualifiers
        admission = sorted(chosen, key=lambda i: (i not in qualifiers, i)) if qualifiers_first else sorted(chosen)
        kept, size = [], 0
        for index in admission:
            line = lines[index]
            if size + len(line[2]) + 1 > max_chars:
                if qualifiers_first:
                    continue                    # try shorter later lines within the cap
                break
            kept.append(index)
            size += len(line[2]) + 1
        selected = [lines[i] for i in sorted(kept)]
        if not selected:
            prefix_end = min(end, start + prefix_chars)
            selected = [(start, prefix_end, text[start:prefix_end])]
    else:
        prefix_end = min(end, start + prefix_chars)
        selected = [(start, prefix_end, text[start:prefix_end])]
    spans = [{"start": a, "end": b} for a, b, _ in selected]
    return "\n".join(piece for _, _, piece in selected), spans, [piece for _, _, piece in selected]


def _subject(text: str, location: Optional[str]) -> Optional[str]:
    front = re.search(r"(?m)^name:\s*(.+?)\s*$", text[:400]) if text.startswith("---") else None
    if front:
        return front.group(1)
    heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if heading and not heading.group(1).startswith(("repo:", "space:")):
        return heading.group(1)
    if location:
        return location.split(":", 1)[-1].rstrip("/") or None
    return None


def _attribute(selected_lines: list[str]) -> Optional[str]:
    for line in selected_lines:
        if _is_assertion(line) and not QUALIFIER.search(line):       # a value, not its qualifier
            match = ASSIGNMENT.search(line)
            if match:
                return match.group(1)
    return None


def build_record(layout: str, ref: dict[str, Any], row: Any, query: str) -> dict[str, Any]:
    """One item record for `state["items"][qid]`, from a broker-read hub row."""
    start, end = int(ref["start"]), int(ref["end"])
    if layout == STATE_V1:
        return {"source_id": ref["source_id"], "version": row.version, "environment": row.environment,
                "text": row.text[start:end][:MAX_EXCERPT_CHARS]}
    if layout == STATE_V2_COMPACT:
        excerpt, spans, selected = excerpt_of(row.text, start, end, query, COMPACT_EXCERPT_CHARS,
                                              COMPACT_EXCERPT_CHARS, qualifiers_first=True)
    else:
        excerpt, spans, selected = excerpt_of(row.text, start, end, query)
    return {"source_id": ref["source_id"], "artifact_id": row.artifact_id, "version": row.version,
            "environment": row.environment, "subject": _subject(row.text, row.location),
            "attribute": _attribute(selected), "assertion_role": ROLE_BY_SOURCE.get(ref["source_id"]),
            "excerpt": excerpt, "excerpt_spans": spans}
