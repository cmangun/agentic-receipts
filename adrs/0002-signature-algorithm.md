# ADR-0002: Signature algorithm and post-quantum migration path

**Status**: Accepted
**Date**: 2026-04-28

## Context

Receipts in this suite carry signatures that bind each receipt to an identifiable signing principal. The signature scheme has two non-trivial requirements that interact: it must be **deterministic** (the same input under the same key must produce the same signature byte-for-byte across signing operations and across implementations), and it must have a credible **post-quantum migration path** because every hash-chained record signed today is implicitly archived — signatures retroactively weaken when their underlying primitive is broken.

Determinism is a hard requirement, not a preference. Hash-chained records canonicalize their bodies to enable identical re-hashing across implementations; non-deterministic signature schemes (ECDSA in its standard form, for example) produce different signature bytes on each signing operation, which cannot survive canonicalization without introducing implementation-specific re-signing that compromises verifier portability.

Post-quantum readiness is a long-horizon concern. v0.1 ships under classical assumptions (SHA-256 collision resistance, Ed25519 forgery resistance) per the threat model at `agentic-receipts/spec/threat-model.md` §8. The migration plan must not strand v0.1 adopters when the post-quantum migration occurs — it must layer a second signature alongside the existing classical one, not replace it.

The deciding constraint is deterministic signing as a hard requirement; post-quantum migration as a planned v0.2 deliverable, not a v0.1 commitment.

## Decision

Use Ed25519 (RFC 8032) as the signature scheme for the v0.1 release line. Plan a dual-signature scheme (Ed25519 plus Dilithium3 or an equivalent post-quantum signature) for v0.2, with bundles signed pre-migration remaining verifiable against archived Ed25519 keys after migration.

## Alternatives Considered

- **ECDSA-P256 (NIST P-256)**: Broader regulatory recognition than Ed25519; well-established in TLS and PKI ecosystems. Rejected because ECDSA's standard signature scheme is non-deterministic — the same input under the same key produces different signatures across signing operations. Non-determinism is a footgun for hash-chained records: signature variance breaks the canonicalization assumptions that enable byte-identical re-verification across implementations.
- **RSA-PSS-2048**: Most widely deployed signature scheme; required by some legacy regulatory frameworks. Rejected because of signature size — RSA-PSS at 2048 bits produces 256-byte signatures versus Ed25519's 64-byte signatures, inflating every receipt by approximately 200 bytes. At session-scale receipt counts (10² to 10⁴ receipts), bundle size becomes a bottleneck before verification cost; the size penalty is paid every time a bundle is exported, transmitted, or archived.
- **Dilithium3 alone (no classical signature)**: Future-proof against post-quantum attacks today. Rejected on ecosystem-readiness grounds — verifier libraries in mainstream stacks (Rust, TypeScript, Python) do not yet have stable, audited Dilithium3 implementations. Adopting Dilithium3 alone would strand v0.1 implementers behind a thin and shifting library surface. Ed25519 plus a planned Dilithium3 dual-signature for v0.2 is the migration path that keeps v0.1 adopters supported while adding post-quantum hardness when the ecosystem matures.
- **Ed448**: Larger key, more conservative security margin than Ed25519 (224-bit security versus 128-bit). Rejected because Ed25519's security margin is sufficient through the v0.1 timeframe, while Ed448 costs more (larger signatures, slower keygen) for a security gain that is unmeasurable in real-world terms.

## Consequences

### Positive

- Deterministic signing enables byte-identical receipts across implementations and over time, preserving the verifiability property that makes cross-implementation conformance vectors meaningful.
- Compact signatures (64 bytes per receipt) keep bundle sizes manageable at session scale; archival cost remains predictable.
- Ed25519 has wide ecosystem support — verifier libraries are mature in all three reference implementation languages, with stable APIs and well-understood security properties.

### Negative

- v0.1 ships under classical cryptographic assumptions. The post-quantum vulnerability horizon is bounded but real; bundles signed today are at risk if a cryptographically-relevant quantum computer emerges before the v0.2 dual-signature migration completes. Documented as a residual risk in `agentic-receipts/spec/threat-model.md` §8.
- The dual-signature migration in v0.2 will require coordinated tooling work across the suite — signers, verifiers, and key-history files all need updates. The migration's stability classification is governed by `VERSIONING.md` §6 (stability markers and experimental fields).