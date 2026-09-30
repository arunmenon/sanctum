# Section map

[Overview](README.md) · [HLD](hld.md)

Each section has one owning page. Sections are numbered 1 to 14 across the architectural proposal, the memory design and the contracts page; the System One providers page has its own sections, referred to as Providers §1 to §14.

| Section | Title | Page |
|---|---|---|
| 1 | Summary | [Architectural proposal](hld.md#section-1) |
| 2 | Problem | [Architectural proposal](hld.md#section-2) |
| 3 | Goals | [Architectural proposal](hld.md#section-3) |
| 4 | Principles | [Architectural proposal](hld.md#section-4) |
| 5 | Architecture | [Architectural proposal](hld.md#section-5) |
| 5.1 | The journey of one question | [Architectural proposal](hld.md#section-5-1) |
| 5.2 | Two pillars inside a given boundary | [Architectural proposal](hld.md#section-5-2) |
| 5.3 | Components | [Architectural proposal](hld.md#section-5-3) |
| 6 | Decision layer | [Architectural proposal](hld.md#section-6) |
| 6.1 | Why a System One model | [Architectural proposal](hld.md#section-6-1) |
| 6.2 | What a single Jev call looks like | [Architectural proposal](hld.md#section-6-2) |
| 6.3 | Decisions run in rounds | [Architectural proposal](hld.md#section-6-3) |
| 6.4 | Decision catalog | [Architectural proposal](hld.md#section-6-4) |
| 6.5 | Escalation: a funnel, not a ladder everyone climbs | [Architectural proposal](hld.md#section-6-5) |
| 6.6 | Decision result contract | [Architectural proposal](hld.md#section-6-6) |
| 6.7 | Calibration | [Architectural proposal](hld.md#section-6-7) |
| 7 | Evidence and authority | [Architectural proposal](hld.md#section-7) |
| 7.1 | Evidence unit | [Architectural proposal](hld.md#section-7-1) |
| 7.2 | Authority is a declaration about a kind of fact | [Architectural proposal](hld.md#section-7-2) |
| 7.3 | Ranking | [Architectural proposal](hld.md#section-7-3) |
| 7.4 | Packing into the budget | [Architectural proposal](hld.md#section-7-4) |
| 7.5 | Version applicability and exact copies | [Architectural proposal](hld.md#section-7-5) |
| 8 | Read path | [Architectural proposal](hld.md#section-8) |
| 9 | Anticipated questions | [Architectural proposal](hld.md#section-9) |
| 10 | Open decision | [Architectural proposal](hld.md#section-10) |
| 11 | What memory holds | [Memory and meta-taxonomy](memory-design.md#section-11) |
| 11.1 | In one sentence | [Memory and meta-taxonomy](memory-design.md#section-11-1) |
| 11.2 | Not to be confused with Engram | [Memory and meta-taxonomy](memory-design.md#section-11-2) |
| 11.3 | Five kinds of memory | [Memory and meta-taxonomy](memory-design.md#section-11-3) |
| 11.4 | A thin ontology in three layers | [Memory and meta-taxonomy](memory-design.md#section-11-4) |
| 11.5 | Names, subjects, and places are different things | [Memory and meta-taxonomy](memory-design.md#section-11-5) |
| 11.6 | Schema v0 | [Memory and meta-taxonomy](memory-design.md#section-11-6) |
| 11.7 | Allowed uses of each relation | [Memory and meta-taxonomy](memory-design.md#section-11-7) |
| 11.8 | A real neighborhood: payment-auth | [Memory and meta-taxonomy](memory-design.md#section-11-8) |
| 11.9 | Why a graph, and why not smaller? | [Memory and meta-taxonomy](memory-design.md#section-11-9) |
| 11.10 | Attributed subjects: `Artifact ABOUT Entity` in operation | [Memory and meta-taxonomy](memory-design.md#section-11-10) |
| 12 | How memory is built and used | [Memory and meta-taxonomy](memory-design.md#section-12) |
| 12.1 | Where the knowledge comes from | [Memory and meta-taxonomy](memory-design.md#section-12-1) |
| 12.2 | Resolving names: identity, ambiguity, no guessing | [Memory and meta-taxonomy](memory-design.md#section-12-2) |
| 12.3 | Per-source query plans | [Memory and meta-taxonomy](memory-design.md#section-12-3) |
| 12.4 | Procedures: a small grammar and a precedence ladder | [Memory and meta-taxonomy](memory-design.md#section-12-4) |
| 12.5 | How the router uses memory, with failure behavior | [Memory and meta-taxonomy](memory-design.md#section-12-5) |
| 12.6 | Memory releases | [Memory and meta-taxonomy](memory-design.md#section-12-6) |
| 12.7 | Governance | [Memory and meta-taxonomy](memory-design.md#section-12-7) |
| 12.8 | Does memory have enough context? | [Memory and meta-taxonomy](memory-design.md#section-12-8) |
| 12.9 | Schema evolution and reconstruction | [Memory and meta-taxonomy](memory-design.md#section-12-9) |
| 12.10 | How memory improves: a gated loop | [Memory and meta-taxonomy](memory-design.md#section-12-10) |
| 13 | Worked examples | [Contracts and worked scenarios](contracts-and-scenarios.md#section-13) |
| 14 | Contracts | [Contracts and worked scenarios](contracts-and-scenarios.md#section-14) |
| 14.1 | Request | [Contracts and worked scenarios](contracts-and-scenarios.md#section-14-1) |
| 14.2 | Caller modes | [Contracts and worked scenarios](contracts-and-scenarios.md#section-14-2) |
| 14.3 | Evidence response | [Contracts and worked scenarios](contracts-and-scenarios.md#section-14-3) |
| 14.4 | Backend adapter contract | [Contracts and worked scenarios](contracts-and-scenarios.md#section-14-4) |

**Worked examples** ([§13](contracts-and-scenarios.md#section-13)): Examples 1 to 13, the worked trace, and Fixtures 14 to 21.

| Providers section | Title |
|---|---|
| Providers §1 | [The cascade and where providers sit](system-one-providers.md#1-the-cascade-and-where-providers-sit) |
| Providers §2 | [Provider interface](system-one-providers.md#2-provider-interface) |
| Providers §3 | [Wire protocol: `POST /v1/systemone`](system-one-providers.md#3-wire-protocol-post-v1systemone) |
| Providers §4 | [Mapping Sanctum decisions to primitives](system-one-providers.md#4-mapping-sanctum-decisions-to-primitives) |
| Providers §5 | [The handshake: thirteen points](system-one-providers.md#5-the-handshake-thirteen-points) |
| Providers §6 | [Isolation: the System One broker](system-one-providers.md#6-isolation-the-system-one-broker) |
| Providers §7 | [What the model can and cannot lose](system-one-providers.md#7-what-the-model-can-and-cannot-lose) |
| Providers §8 | [Calibration binding and the shadow-only rule](system-one-providers.md#8-calibration-binding-and-the-shadow-only-rule) |
| Providers §9 | [Conformance checks for a "supported" backend](system-one-providers.md#9-conformance-checks-for-a-supported-backend) |
| Providers §10 | [Retention](system-one-providers.md#10-retention) |
| Providers §11 | [Batching](system-one-providers.md#11-batching) |
| Providers §12 | [Round 3 decisions (D6 conflict, D4 relevance)](system-one-providers.md#12-round-3-decisions-d6-conflict-d4-relevance) |
| Providers §13 | [The two integrated providers](system-one-providers.md#13-the-two-integrated-providers) |
| Providers §14 | [Template and state-layout registry](system-one-providers.md#14-template-and-state-layout-registry) |
