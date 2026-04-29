# ADR-0004: JSON canonicalization rules

**Status**: Accepted
**Date**: 2026-04-28

## Context

Receipts in this suite are hash-chained, and the hash of each receipt is computed over its serialized body. For the chain to verify identically across implementations and over time, two correct implementations of the spec must produce **byte-identical** serialized output for the same logical receipt. Any divergence — whitespace, key ordering, float representation, Unicode normalization — breaks chain verification at the implementation boundary.

JSON is the chosen serialization format for the suite, established by the receipt schemas in `agentic-receipts/spec/`. JSON is human-readable, debuggable in any text editor, and ships with default tooling in every reference implementation language. But raw JSON has well-known canonicalization hazards: object key ordering is unspecified, whitespace is permissive, numeric representations are ambiguous (especially for floats and large integers), and string Unicode handling varies across implementations.

Two further forces shape the choice. **Standards precedent** matters because canonicalization edge cases are a known footgun — projects that wrote their own canonicalization (early Bitcoin, several blockchain projects) hit exactly the issues that an established standard has already settled. **Human readability** of the verification surface matters because auditors and engineers debugging bundles need to read evidence directly without specialized tooling.

The deciding constraint is standards-precedent plus human-readability of the verification surface.

## Decision

Use JCS (JSON Canonicalization Scheme, RFC 8785) for deterministic JSON serialization across all receipts, decision receipts, artifact manifests, and bundle-level documents. Specific JCS rules — UTF-8 normalization, lexicographic key ordering, restricted number representation, no insignificant whitespace — are documented in `agentic-receipts/spec/canonicalization.md`.

## Alternatives Considered

- **Custom canonicalization (project-specific rules)**: Full control over edge cases; rules tuned to the suite's specific needs. Rejected on standards-precedent risk. Projects that wrote their own canonicalization — early Bitcoin and several subsequent blockchain projects — hit edge cases (Unicode normalization, float representation, integer boundary conditions) that an IETF standard has already settled. Reinventing canonicalization is a known footgun, with cryptographic exploits as the cost of getting it wrong.
- **CBOR with deterministic encoding (RFC 8949)**: Binary serialization, more compact than JSON, unambiguous by design (CBOR's deterministic encoding is normative, not optional). Rejected on tooling-ecosystem friction. Despite being technically superior in compactness and unambiguity, JSON tooling is universal; adopters can debug JSON in any text editor, paste it into a verifier, or read it during an audit without specialized parsers. CBOR requires dedicated tools at every step. For a verifiability surface where humans need to read evidence, JSON's debuggability outweighs CBOR's technical advantages.
- **Protocol Buffers with deterministic serialization**: Schema-first serialization with strong typing and compact wire format. Rejected on schema-evolution conflict with the suite's existing versioning model. Protocol Buffers' schema-versioning approach (field numbers, reserved ranges, default-value semantics) conflicts with the receipt schema-versioning model defined in `VERSIONING.md` §4 (explicit `schema_version` SemVer field at chain root and per receipt). Layering two versioning schemes on top of each other is a maintenance hazard and creates ambiguity about which one is authoritative when they disagree.

## Consequences

### Positive

- IETF-standard canonicalization with formal published rules; edge cases (Unicode, floats, integer boundaries) are settled by the standard rather than reinvented per implementation.
- Human-readable serialized form. Auditors, regulators, and engineers can read receipt JSON directly during inspection without specialized tools.
- Wide tooling ecosystem — JCS implementations exist in Rust, TypeScript, Python, Go, and Java; JSON parsers are universal even where JCS-specific tooling is not.

### Negative

- JSON's verbosity compared to CBOR or Protocol Buffers — receipts and bundles are larger on disk and on the wire. Acceptable at session scale; relevant at archive scale, where bundle compression at the storage layer is the standard mitigation.
- JCS's specific rules around number representation will be restrictive for some adopters. JCS does not permit JSON numbers requiring more than 53 bits of precision, and floats canonicalize to specific normalized forms; integer types beyond 2^53 must be encoded as strings. Restrictions are documented in `agentic-receipts/spec/canonicalization.md` so adopters can design schemas around them.
- Implementations must ship a JCS canonicalizer or wrap an existing library. The spec's reference vectors test canonicalization explicitly to surface implementation bugs early.