# Slack note: Sanctum HLD v5.3.1

Team, a short note on the Sanctum HLD.

We have extended the initial scaffold into a design foundation for the research MVP. It is tagged `design-v5.3.1` and lives here: https://github.com/arunmenon/sanctum/tree/design-v5.3.1/design/intelligence-layer

Scope for now is deliberately narrow: routing intelligence only. Two pillars:
- **Memory and ontology**: what Sanctum remembers about sources (names, subjects, places, procedures, releases), and why only reviewed names establish identity.
- **System 1 cascade**: rules first, then a cheap decision model behind one provider interface, with a safe default whenever the model is uncertain. What the model may and may not change is stated per decision.

Access control, writes and replay are treated as given inputs, not designed here.

Where to read, in order (about an hour):
1. `README.md`: scope and reading guide
2. `hld.md`: the request journey, the two pillars, the decision layer (§5 to §7)
3. `memory-design.md`: the ontology and how memory is built and used (§11 to §12)
4. `system-one-providers.md`: the decision-model handshake, providers and calibration
5. `contracts-and-scenarios.md`: worked examples, including one full trace from question to evidence

What I need from you: read with your own hub in mind and tell me where the ontology or the cascade would not fit it. The one open decision is in `hld.md` §10 (how many extra source calls a missed fact is worth).

Comments as PRs against the `design/` folder, or in this thread.
