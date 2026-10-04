# Identity and ledger developer packet

Produce two fictional Python artifacts as JSON `artifacts` with `path`, `title`, `version`, `text`, plus an `introduced_claims` audit list. One is an identity request schema; one is a ledger consumer. Do not include benchmark language or private identifiers.

Identity local context: a fraud request needs tenant and authenticated-subject context. Identity authorization and payment authorization are different services; teams sometimes call either “Auth.” You do not own the payment timeout policy. Preserve that boundary in comments rather than inventing it.

Ledger local context: only approved payment authorizations may create postings. A proposed pending-review status must not produce a ledger posting. The ledger consumer's current accepted event is approved authorization. You do not know the canary duration or timeout deadline. Distinguish an interface concern about unknown new statuses from an observed defect.

Make the code plausible, with service-specific vocabulary and partial documentation, rather than a polished summary of the whole scenario. Mark additional assumptions separately.
