# Security and Live-Event Test Matrix

Use the real backend where possible. The UI is untrusted and cannot upgrade state.

| Boundary | Required assertion |
|---|---|
| Pending decision | Execute request is rejected or returns `EXECUTION_DENIED`. |
| Rejected decision | Execute request cannot succeed. |
| Claimed authority | Forged `claimed_authority` is ignored and cannot grant authority. |
| Ratification | Permission alone cannot make an unratified decision executable. |
| Epistemic state | Local edits cannot turn `INFERRED` into `VERIFIED`. |
| AI Shadow | Every item remains `authority=NONE`, `can_execute=false`, `can_ratify=false`. |
| Ledger | Client cannot mutate historical events, sequences, hashes, or replay state. |
| Capability | Missing/invalid capability blocks execution. |
| SSE | Receiving an event triggers refetch; it is never treated as proof that the client caused a mutation. |
| Memory capture | Unauthorized capture is rejected; canonical persistence is server-side. |
| Shadow proposal | A recommendation creates only a governed proposal and records Shadow authority as `NONE`. |

Also test network failure, malformed event payloads, stale state labels, reconnect/resynchronization, and that unavailable backend features produce an honest support message instead of fake data.
