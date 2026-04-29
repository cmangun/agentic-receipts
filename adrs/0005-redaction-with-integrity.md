# ADR-0005: Redaction-with-integrity model

**Status**: Accepted
**Date**: 2026-04-28

## Context

Receipts in this suite often contain sensitive data — PHI in healthcare contexts, PII in consumer-facing systems, commercially-sensitive data in enterprise integrations. Bundles produced by such systems cannot flow to all auditors with all field values intact: an external auditor reviewing a regulatory submission may need to see that a receipt exists, what type of action it represents, what the policy decision was, and that the chain integrity holds, without seeing the patient name or account number recorded inside.

The redaction mechanism must satisfy two requirements that interact. **Hash integrity preservation**: redaction must not break the chain. A bundle whose chain breaks because fields were removed is no longer verifiable, defeating the purpose of redaction-aware export. **Audit-signal preservation**: the fact that redaction occurred, where it occurred, and what categories of fields were redacted must remain visible to verifiers — silent redaction allows operators to selectively remove incriminating evidence without leaving an auditable trail.

The misuse vectors enumerated in `agentic-receipts/spec/threat-model.md` §5 (selective redaction of incriminating fields, redaction of timestamps to obscure ordering, redaction-map tampering) shape the design: the mechanism must produce a redacted bundle that still functions as primary evidence of *the fact of redaction*, not just of the surviving values.

The deciding constraint is practical cryptographic readiness at v0.1, plus preserving the audit signal of redaction events.

## Decision

Hash-replacement with field-name preservation, paired with a bundle-level audit trail. A redacted field's value is replaced with a hash placeholder computed from the original value plus a per-field salt; the field name remains visible in the receipt body. Each redacted receipt carries an inline `_redacted` array listing the names of removed fields (the leading underscore signals non-canonical metadata per the convention in `VERSIONING.md` §6). A separate bundle-level `redaction-map.json` carries the full audit trail: which fields were redacted on which receipts, when, by which operator-identifying token, signed by the redacting operator.

## Alternatives Considered

- **Selective disclosure with BBS+ signatures**: Cryptographic primitive that preserves the *semantics* of redacted values via verifiable predicates (an auditor can verify "this redacted field was a `deny` decision" without seeing the field). Rejected on practical readiness at v0.1. The cryptographic primitive is sound, but library support across Rust, TypeScript, and Python is thin (one mature implementation each, at best); execution-volume performance has not been measured at receipt scale; integration overhead is non-trivial. Promising for v0.2 revisit, not ready for v0.1.
- **zkSNARK proofs over redacted predicates**: Preserves *assertions* about redacted values without revealing them, using zero-knowledge proofs over pre-defined predicate circuits. Rejected on a similar readiness gap, plus circuit-design overhead. A zkSNARK that proves "this redacted decision was a deny" requires pre-defined predicate circuits; agents emit receipts under arbitrary policies whose predicates are not knowable in advance. Doesn't fit the workload shape for v0.1.
- **Whole-receipt removal with chain-skip mechanism**: Removes the receipt entirely, leaving a visible gap-marker in the chain. Rejected on audit-trail loss. A receipt's existence and its position in the chain are themselves audit-relevant — concentrated removals are a finding pattern per the threat model. Hiding the existence of receipts removes that signal entirely; auditors lose the ability to detect "operator redacted 47 receipts in this session" because the receipts are no longer detectable as having existed.

## Consequences

### Positive

- Hash integrity is preserved across redaction. The chain verifies cleanly; the only modification is the value substitution at known field positions.
- The fact of redaction is preserved as an audit signal. Auditors see the `_redacted` array per receipt and the bundle-level `redaction-map.json` audit trail; concentrated redactions on specific field types remain visible as a finding pattern.
- The mechanism uses standard cryptographic primitives (SHA-256 with per-field salts) that ship in every reference implementation language. No specialized library dependencies.

### Negative

- Redacted values are gone — not recoverable, not provably-X, not partially disclosed. Redaction trades off recoverability for hash integrity. Adopters who need value-preserving selective disclosure (e.g., proving a redacted decision was a `deny` without revealing the policy reason) are not served by v0.1's redaction mechanism.
- v0.2 BBS+ exploration is on the roadmap for adopters who need value-preserving selective disclosure; the v0.1 redaction approach remains supported alongside any future selective-disclosure addition.
- Operators implementing redaction must maintain their own redaction-policy infrastructure (which fields to redact, under what conditions, with what audit trail). The suite specifies the *mechanism* for redaction-with-integrity; the *policy* of when to apply it is an operator concern.