# ADR-0003: Hash chain versus Merkle tree for ordering proof

**Status**: Accepted
**Date**: 2026-04-28

## Context

Receipts in this suite must carry cryptographic proof of ordering: a verifier examining a bundle must be able to detect not only individual receipt tampering but also reordering, dropped records, and silent insertion. The structural choice — how receipts commit to their position in the sequence — is one of the load-bearing design decisions in the spec layer. This decision interacts directly with the architectural principle stated in `REFERENCE-ARCHITECTURE.md` §3: append-only is enforced by cryptographic property of the records themselves, not by storage promises.

The workload shape of agent execution is **append-as-you-go**: an agent emits receipts as actions execute, with no a-priori knowledge of how many receipts the session will produce or when it will end. A receipt produced at t=3 must be verifiable as part of the chain immediately, not after a session-end finalization step.

Two further forces shape the choice. **Self-containment** of the verifiability claim — the suite explicitly avoids third-party trust dependencies for ordering attestation, per the threat model. **Future-extensibility** — archive-scale verification cost is a known concern, deferred to v0.2 by design, but the v0.1 ordering primitive must not preclude future optimizations.

The deciding constraint is append-friendly writes for streaming agent execution.

## Decision

Use hash-chained receipts: each receipt body includes a `previous_hash` field referencing the SHA-256 hash of the immediately prior receipt. The chain root is the first receipt's hash; chain integrity is verified by re-hashing each receipt and comparing the result to the next receipt's `previous_hash`. Not a Merkle tree.

## Alternatives Considered

- **Merkle tree (binary, SHA-256 leaves)**: Standard transparency-log primitive used by Certificate Transparency, Sigstore, and most published audit-log systems. Rejected on workload-shape mismatch: Merkle gives batch-verification efficiency (O(log n) inclusion proofs) but requires knowing the full tree before any single receipt is verifiable. Agents emit receipts as they execute — append-as-you-go is the actual use case. A Merkle approach would force buffering until session end or out-of-order finalization, both of which conflict with the verify-as-you-go property the chain provides.
- **Skip-chain (hash chain with periodic checkpoint commits)**: Hybrid approach that preserves append-friendly writes while adding sub-linear verification through periodic checkpoints. Rejected as scope creep at v0.1: skip-chain checkpoints solve archive-scale verification cost, and v0.1 punts archive-scale to v0.2 by explicit design. Adding skip-chain now is premature optimization for a use case the v0.1 release line does not target.
- **Signed timestamp service (TSA, RFC 3161)**: Outsourced ordering proof from a trusted third party, with the timestamp service signing each receipt as evidence of its position in time. Rejected as a trust-model violation: the suite's verifiability claims explicitly avoid third-party trust dependencies. A TSA introduces a verifier-side requirement to trust the timestamp service's key, which compromises the offline-verification property bundles are designed to support.

## Consequences

### Positive

- Append-friendly writes match the agent-execution workload exactly. A receipt is fully verifiable the moment it is written; no buffering, no session-end finalization, no out-of-order chain construction.
- Self-contained verification — a bundle plus the issuing public key is sufficient to verify the entire chain offline, with no third-party trust dependency.
- Cryptographic detection of reordering, dropping, and silent insertion. Any modification to chain structure breaks the `previous_hash` linkage at the modified position, with the failure locatable to the specific receipt index.

### Negative

- Linear verification cost: O(n) for n receipts, where Merkle would offer O(log n) for batch inclusion proofs. At session-scale receipt counts (10² to 10⁴) the difference is invisible; at archive scale (10⁶+) this becomes a real concern.
- v0.2 addresses archive-scale verification through optional checkpoint receipts as a documented extension to the chain primitive. The extension is additive and does not break v0.1 chain structure.
- No native batch-inclusion proofs for sub-chain verification (e.g., "prove this set of 100 receipts is part of a 1M-receipt chain without re-hashing the whole chain"). Adopters needing this property today implement it at the application layer using standard chain-walking techniques.