# Owner manifests (lab plan §5.3)

Written the way hub owners would write them: from what each hub exposes (`capabilities.json`,
`list_repos`, `list_tree`, `list_spaces` output, tool descriptions) plus owner declarations
(authority per fact kind, which access groups a place is shared with, must-consult procedures).
They are deliberately incomplete: no service aliases, no per-service selectors, no incident hub
entry (IncidentHub is held back until M7). `sanctum_ref` loads them as its registry; a missing or
invalid registry fails closed.

Access groups are owner declarations, not hub-visible structure: an owner knows which groups a
place is shared with. They let Sanctum report a denied must-consult source without calling it.
