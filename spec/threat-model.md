# Threat Model

> v2. Pinned positions inherited from `REFERENCE-ARCHITECTURE.md` §7: trusted runtime + in-process signing key; chain integrity primary, storage append-only secondary; replay defeated by chain context (primary) + `correlation_id` uniqueness (secondary); redaction tracked via inline `_redacted` array (per-receipt) and a separate redaction-map file (bundle-level).

*Companion to `REFERENCE-ARCHITECTURE.md` §7. This document is the canonical adversary model for v0.1 — what verifiability claims hold against whom, and where they don't.*

## §1. Scope and assumptions

This threat model defines the adversary against which the Evidence Suite's verifiability claims hold, and names where they do not. It is the canonical reference for what a v0.1 bundle proves under what assumptions. Component repositories that emit, consume, or verify receipts inherit these assumptions; deviations are documented as ADRs in the repo affecting the deviation.

**Trust model.** The agent runtime is trusted to emit honest receipts, with signing keys held in-process by the runtime operator. This matches the deployment shape of essentially all current regulated AI systems: the operator owns the runtime and is the signing principal. Malicious-runtime scenarios are addressed as a separate adversary class, not as the v0.1 default. A trusted-execution-environment-backed signing path is sketched for v0.2 but is not in scope here.

**Storage trust.** Storage layers are not trusted to enforce append-only properties. The hash chain enforces append-only by construction; storage advice is defense-in-depth. Adopters use ordinary storage substrates and rely on the chain to catch tampering.

**Verifier trust.** Verifiers trust the public key associated with the signing identity, fetched and validated through a signed key-history mechanism (described in `REFERENCE-ARCHITECTURE.md` §7). Verification is offline against the bundle and key-history; no live communication with the producing system is required or expected.

## §2. Adversary capabilities and non-capabilities

The adversary in this model is a party motivated to falsify the record of agent execution, conceal events, or pass forged records as authentic. The model assumes capability bounds drawn from current cryptographic practice and the trust shape established above.

**The adversary can:**

- Tamper with bundles in transit or at rest.
- Drop or reorder records in storage.
- Synthesize records claiming to come from a known signer (without holding the key).
- Compromise an old signing key and use it on records dated within the compromise window.
- Submit previously-emitted bundles or individual receipts for re-validation (replay).
- Strip portions of a record body via the redaction mechanism while preserving hash integrity.

**The adversary cannot, within v0.1's assumptions:**

- Compromise the runtime's *current* signing key without detection. Runtime key custody is a deployment concern that adopters address through their own key-management infrastructure (HSM, KMS).
- Forge SHA-256 collisions or break Ed25519 signatures. Both are assumed within their published security parameters through the v0.1 timeframe.
- Modify a receipt mid-chain without breaking the chain's hash integrity, regardless of access to the signing key.
- Re-sign and re-chain a bundle to disguise tampering without detection by a verifier holding the key history.

**Out of scope for v0.1.** Side-channel attacks on the signing key (timing, power analysis, fault injection) are outside this model — they are deployment-level concerns for the operator's HSM/KMS setup. Detection of compromise *before* rotation (real-time anomaly monitoring on signing volume or receipt patterns) is also a deployment-level control; the suite's contribution is post-hoc detectability via the key-history record once compromise is known.

## §3. Threat: signing-key compromise

A compromised signing key allows an adversary to produce records that verify as authentic against the key's public counterpart. The threat model addresses how the suite contains the blast radius of compromise rather than preventing it; prevention is the operator's key-management responsibility.

**Compromise window.** From the moment a key is compromised to the moment a rotation entry signed by the previous key (or by an out-of-band recovery key declared at suite setup) is committed to the key-history file. During this window, the adversary can produce convincing forgeries. After the rotation entry, bundles signed by the new key chain to the previous one through the key-history; bundles signed by the compromised key after the rotation are rejected by verifiers reading the up-to-date key history.

**Blast radius.** Only bundles signed by the compromised key during the compromise window are invalidated. Historical bundles signed by the same key *before* the compromise remain trustworthy if the rotation timeline is verifiable. Auditors examining a historical bundle check its claimed sign-time against the key-history's "valid from / valid until" range and accept the bundle if it falls inside the pre-compromise window. The chain integrity of historical bundles is unaffected by future key compromise.

**Recovery path.** The operator publishes a new public key, signs a rotation entry with the previous key (or with the declared recovery key), and commits the entry to the key-history file. Verifiers fetch the updated key-history at next verification and apply the new key going forward. The previous key's public counterpart remains in the key-history indefinitely so historical bundles continue to verify.

**Residual risk.** If compromise is undetected before rotation, adversary-signed bundles inside the window verify as authentic. Detection mechanisms (anomaly monitoring, signing-volume spikes, key-usage audits) are deployment-level controls outside the suite. The suite's contribution is post-hoc detectability through the key-history record once compromise is known and the rotation lands.

**Open: recovery-key handling.** The "recovery key declared at suite setup" pattern requires its own custody discipline distinct from the operational signing key. v0.1 documents the pattern but does not pin recovery-key requirements (HSM-backed? air-gapped? threshold-shared?); deferred to v0.2.

## §4. Threat: replay attacks

Replay attacks resubmit previously-emitted records — a single receipt, a portion of a chain, or an entire bundle — to a verifier that does not maintain context about which records have been seen before. The suite addresses replay through two mutually-reinforcing mechanisms; chain context is the primary cryptographic defense, and `correlation_id` uniqueness is the secondary identifier-based defense.

**Primary: chain-context binding.** Each receipt's `previous_hash` field cryptographically commits the receipt to its position in a specific chain. A receipt removed from its chain and presented in isolation cannot be re-inserted into a different chain — its `previous_hash` would not match the new chain's prior receipt. Replay of a single receipt into a different session fails verification at the chain step. Replay of a contiguous segment fails the same way at the boundary where the segment is grafted onto an unrelated chain.

**Secondary: `correlation_id` uniqueness.** Each chain root carries a unique `correlation_id`, established by the runtime at session start. A bundle replayed wholesale — with its chain context intact — is recognizable by `correlation_id` collision against verifier-side records of previously-seen bundles. Verifiers maintaining a short replay-detection cache reject the duplicate.

**What replay can accomplish.** Limited to wholesale bundle resubmission against a stateless verifier that does not maintain replay-detection state. In that narrow case, the verifier accepts the bundle as authentic — which is correct, because the bundle *is* authentic — but cannot distinguish it from the original submission. Whether this matters depends on what the verifier is for; an audit-trail consumer accepts the same bundle twice without harm, while an authorization workflow keyed on receipts must enforce one-time-use semantics outside the suite.

**What replay cannot accomplish.** Selective replay (extracting a single allow-receipt from one chain and embedding it in another) fails at the chain-context check. Re-targeting a bundle from one verifier to a different one without modification preserves the bundle's authentic state but does not gain anything beyond what the bundle already proves on its own.

**Mitigations available to verifiers.** Time-bounded `correlation_id` caches; replay-detection at the application layer keyed on bundle root hash; per-verifier nonce challenges where the bundle is submitted in an interactive workflow.

## §5. Threat: redaction misuse

Redaction allows an operator to remove sensitive field values from receipts while preserving the hash integrity of the chain. The mechanism is necessary — receipts often contain PHI, PII, or commercially-sensitive data that cannot flow to all auditors — but it is also a misuse vector if not bounded. The suite defines what redaction can and cannot conceal, and exposes both metadata about what was redacted and audit trails recording when.

**What redaction is.** Selective field removal where the original value is replaced by a hash placeholder, allowing chain integrity to be verified without revealing the redacted content. Two visibility surfaces:

- **Inline `_redacted` array (per-receipt).** Each receipt that has been redacted carries a top-level `_redacted` field listing the *names* of removed fields. The leading underscore signals non-canonical metadata per the convention pinned in `VERSIONING.md` §6 of the meta-repo. Field names remain visible; values are gone.
- **Redaction-map file (bundle-level).** A separate `redaction-map.json` at the bundle level carries the full audit trail: which fields were redacted on which receipts, when, by which operator-identifying token. The map is signed by the redacting operator and itself verifiable.

**What redaction cannot conceal.**

- **Existence of an event.** Each receipt's position in the chain is preserved; redacting a receipt removes its body but the slot remains and is detectable.
- **Receipt count.** The chain length is fixed at write time; redaction does not delete records.
- **Causality.** Cross-references between receipts (decision-receipt → action receipt; artifact manifest → action receipt) survive redaction; the redacted body is hidden but the relationships remain visible.
- **The fact of redaction.** A redacted receipt is publicly identifiable as redacted via its `_redacted` array. There is no "silent redaction" mode in v0.1.

**Misuse vectors.**

- **Selective redaction of incriminating fields.** An operator who redacts only fields that would expose policy violations leaves a visible trail in the redaction-map. Auditors detecting a pattern of redactions concentrated on specific field types (e.g., `policy_decision.deny_reason`) treat that as a finding rather than a clean record.
- **Redaction of receipt timestamps to obscure ordering.** Timestamps are part of the canonical body; redacting them removes the value but the receipt's chain position still establishes ordering. Redaction cannot reorder.
- **Redaction-map tampering.** The map is signed by the redacting operator; tampering breaks the signature. A bundle without its map (or with a broken map) is auditable as "redacted but trail missing," again a finding rather than a clean record.

**Open: selective-disclosure crypto.** v0.1 redaction loses content. Selective-disclosure schemes (BBS+ signatures, zkSNARKs in limited domains) preserve the *semantics* of redacted fields while protecting the values. Promising but not yet practical at execution volumes; deferred to v0.2.

## §6. Threat: cross-organization bundle interop

When agent A in organization X invokes an agent or tool in organization Y, the bundle that records the call spans two trust principals. v0.1 does not solve this case; this section names the failure modes and the candidate approaches under design for v0.2.

**Why intra-organizational bundles work and cross-org bundles do not (yet).** The v0.1 trust model assumes a single signing principal — the runtime operator — and a key-history controlled by that operator. A bundle is verifiable against that operator's key. When two operators are involved, the bundle records actions and decisions signed by *different* keys, and a single verifier cannot establish "this is the authentic chain" without knowing both operators' key histories and their relationship.

**Failure modes if cross-org bundles are forced into the v0.1 model.**

- **Single-signer model breaks.** If organization X signs the bundle, the receipts from organization Y's agent are unauthenticated to verifiers who don't trust X to attest for Y. Conversely, if Y signs, X's receipts are unauthenticated to verifiers who don't trust Y to attest for X.
- **Chain integrity ambiguous.** A chain that crosses an organizational boundary mid-session has two valid hash sequences (one from each operator's perspective) but no single signed root that ties them together.
- **Key-history federation undefined.** Verifiers need to know whose key signed what at what time; the current key-history mechanism is single-operator and does not federate.

**Candidate approaches (v0.2 design space).**

- **Federated key disclosure.** Each operator publishes its key-history; bundles spanning operators reference both, and verifiers fetch and validate both. Adds operational coordination but preserves the single-signer per-receipt model. Leading candidate for the document-level interop story.
- **Escrow signers.** A trusted third party (industry consortium, regulator, neutral broker) co-signs cross-org bundles. Adds a trust dependency but resolves the verifier ambiguity. Likely a niche option for regulated environments where a neutral broker exists.
- **Multi-party receipts.** Each receipt carries multiple signatures, one per participating operator. Heaviest scheme; preserves the most decentralization; introduces protocol complexity around key coordination. May be needed for the higher-trust subset of cases.

**v0.1 stance.** Bundles are intra-organizational. Cross-org agent calls are recorded as outbound calls from the perspective of the originating organization, with the response treated as opaque external data (hashed, referenced, but not chained into the originating organization's signed history). The receiving organization records the same call from its perspective in its own bundle. Cross-correlation between the two bundles is at the application layer, not the cryptographic layer.

**Open: which v0.2 candidate wins.** Pinning the v0.2 choice is on the v0.2 roadmap and depends on adoption signals from federation-curious adopters during the v0.1 line.

## §7. Worked example

A worked example of the chain integrity defense, lifted from `REFERENCE-ARCHITECTURE.md` §7:

> An operator suspects a contractor edited a receipt to remove a denied action. The verifier opens the bundle in the viewer; the chain hash check fails at the position of the edit because the next receipt's `previous_hash` no longer matches the tampered record. The viewer flags the failure with the receipt index, the expected hash, and the observed hash. The operator now has a cryptographic claim — not an inference — that tampering occurred, and a specific record to subpoena for further investigation. Without the chain, the same investigation would rely on log-aggregator access logs and storage-layer audit records, both of which are themselves editable; the chain gives the investigator a primary record that does not depend on those.

The example illustrates a key property: the suite's contribution to threat detection is *primary* evidence that does not require corroboration from systems that are themselves attackable. Chain-integrity failures are deterministic, locatable, and survive the loss or compromise of surrounding infrastructure.

## §8. Residual risks and open problems

What v0.1 does not fully address:

- **Post-quantum signature path.** Ed25519 is the v0.1 signing scheme. A dual-signature scheme with Dilithium3 (or equivalent) is on the v0.2 roadmap. Existing chains migrate by adding the new signature alongside the existing Ed25519 signature; verifiers checking both are forward-compatible. Bundles signed pre-migration remain verifiable against archived Ed25519 keys after migration.

- **Cross-organizational bundle interop.** Sketched in §6. Three candidate approaches under design; v0.2 pins one based on adoption signals.

- **Selective-disclosure redaction.** v0.1 redaction loses content. Cryptographic alternatives (BBS+ signatures, zkSNARKs) preserve verifiable assertions about redacted values but are not yet practical at execution volumes. Deferred to v0.2 for revisit.

- **Side-channel attacks on signing keys.** Out of scope; the operator's key-management infrastructure is responsible.

- **Receipt-volume archival at scale.** A high-volume agent emits tens of thousands of receipts per session. Cold-storage and retrieval patterns that preserve verifiability at archive scale are an operational question outside the cryptographic threat model. Practitioner guidance planned for v0.2 documentation.

- **Detection of compromise before rotation.** The suite enables post-hoc detection through key-history records once compromise is known. Real-time anomaly detection (signing volume, unusual receipt patterns) is a deployment-level control, not a property the suite provides.
