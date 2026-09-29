# Memory seed (lab plan §6.4, HLD §8.6)

`ACTIVE` names the active release; `r<N>/release.yaml` is one immutable release. A request pins the
active release at its start; switching releases (or rolling back) is a change of `ACTIVE` only.

Release r1 holds reviewed `DENOTES` names (service-catalog labels, both "Auth Service" skill
namespaces, session-note nicknames), `SELECTS_FOR` places (repos, skill path prefixes, doc
spaces), `MEMBER_OF` for every service, one must-consult procedure (SkillHub for payments
procedure facts), and pinned per-source descriptors. Authority per hub and fact kind stays in
`owners/manifests/`.

Authored from hub-visible structure only. Deliberately incomplete and imperfect, as real memory is:
the MemoryHub name for Ledger Posting is missing, and two skill path selectors do not match the
skills' actual paths. Entity `ref` values are the opaque refs the SUT puts on the wire.
