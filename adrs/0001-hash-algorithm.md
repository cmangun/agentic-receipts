# ADR-0001: Hash algorithm choice

**Status**: Accepted
**Date**: 2026-04-28

## Context

Receipts in this suite are hash-chained: each receipt commits to the prior receipt's hash, and the chain integrity is the suite's load-bearing detection mechanism for tampering, reordering, and omission. The hash function used at every receipt boundary therefore has the largest blast radius of any single cryptographic primitive in the spec layer — a weakness in the hash function compromises the integrity claim retroactively and across every bundle ever produced.

The hash function for v0.1 is selected against three forces. **Regulatory familiarity** in the suite's primary buyer base — FDA-adjacent organizations, CISA-aligned frameworks, FIPS 140-3 validation processes — defaults to the SHA-2 family. **Tooling ecosystem** maturity matters because the suite is a spec that external implementers will adopt: a hash whose libraries ship by default in Rust, TypeScript, and Python lowers the integration tax. **Performance** is tracked but is not the bottleneck at receipt-emission rates; agent sessions emit hundreds to low thousands of receipts, well below the throughput where hash performance becomes load-bearing.

The deciding constraint is regulatory familiarity in the buyer base.

## Decision

Use SHA-256 (FIPS 180-4) as the hash function for receipt chaining, content-addressing, and bundle integrity verification across the v0.1 release line.

## Alternatives Considered

- **BLAKE3**: A modern hash primitive with approximately 5x faster performance than SHA-256 in published benchmarks, used in some newer transparency-log implementations. Rejected because the performance gain is unmeasurable at receipt-emission rates and the regulatory cost is real — FDA-adjacent buyers, CISA frameworks, and FIPS 140-3 validation processes all default to the SHA-2 family. Ecosystem trust outweighs throughput here.
- **SHA-3 (Keccak)**: NIST-standardized successor to SHA-2 (FIPS 202), with a different cryptographic construction (sponge function rather than Merkle-Damgård). Rejected because the verifier-library ecosystem in Rust, TypeScript, and Python ships SHA-256 by default; SHA-3 requires explicit dependencies. For a spec that external implementers must adopt, dependency friction matters.
- **BLAKE2b**: Faster than the SHA-2 family, deployed by Sigstore and Argon2. Rejected on the same regulatory-familiarity argument as BLAKE3 — outside the SHA-2 family means outside the buyer base's default cryptographic vocabulary.

## Consequences

### Positive

- Verifier libraries ship SHA-256 by default across all three reference languages (Rust, TypeScript, Python). External implementers integrate without adding cryptographic dependencies.
- Regulatory and validation frameworks (FIPS 140-3, FedRAMP, FDA pre-market) accept SHA-256 without additional documentation or exception processes.
- Algorithm is well-understood, with extensive cryptanalytic history; security parameters are stable and predictable through the v0.1 timeframe.

### Negative

- Approximately 5x performance hit at the hashing step compared to BLAKE3 in published microbenchmarks. Negligible at receipt-emission rates but real at archive-scale rehashing operations.
- Committed to a hash function whose academic confidence horizon is finite. SHA-256's theoretical weaknesses (collision-search complexity, length-extension attacks) are well-studied but not currently exploitable; the migration story for an eventual replacement is governed by `VERSIONING.md` §5 (breaking changes and deprecation window).
- A future hash-function migration will be a breaking change requiring a major suite version bump and a deprecation window per the suite's SemVer policy.