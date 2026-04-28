# agentic-receipts

> Part of the [Agentic Evidence Suite](https://github.com/cmangun/agentic-evidence) — six interoperating components for verifiable agentic AI. See [`REFERENCE-ARCHITECTURE.md`](https://github.com/cmangun/agentic-evidence/blob/main/REFERENCE-ARCHITECTURE.md) for the suite-level architecture.

Standard receipts and trace semantics for **verifiable agent execution**.

This repo defines:
- Receipt and trace event schemas
- Canonicalization rules for deterministic hashing
- Hash-chaining and signature envelopes
- Redaction semantics that preserve integrity verification
- Test vectors for cross-implementation compatibility

## Why this exists

Most agent systems produce logs. Logs are not verification. This specification defines receipts that can be independently validated to confirm:
1. What the agent did
2. Under which policy constraints
3. What artifacts were produced
4. Whether the record was tampered with

## Core Concepts

- **Trace**: ordered event stream (JSONL) describing agent actions.
- **Receipt**: cryptographic attestation for an event (hash + prev_hash + signature).
- **Bundle**: portable directory containing trace + receipts + artifacts + metadata.
- **Policy Decision**: allow/deny receipt produced by a non-bypassable policy layer.

## Quick Start

- Validate schemas: `./tools/validate_schemas.sh`
- Review examples: `examples/minimal/`
- Use vectors to build verifiers: `vectors/v1/`

## Compatibility

Downstream projects should treat this repo as the canonical source of truth for:
- `schemas/`
- `spec/`
- `vectors/`

## Threat Model

See: `spec/threat-model.md`

## Framework alignment

This spec implements the **receipts and trace semantics layer** of [ATVC — the Agentic Trust Validation Certification framework](https://enterprise-ai-playbook-demo.vercel.app/). Specifically:

| ATVC Phase | Coverage |
|---|---|
| **Phase 02 — Architecture** (steps 26–50) | Receipt schema, canonicalization, hash-chain, signature envelope, redaction model |
| **Phase 03 — Engineering** (steps 51–75) | Conformance test vectors, threat model, validation tooling |

Conformance vectors in `vectors/v1/` are referenceable as ATVC validation artifacts for the Architecture phase-exit contract.

## Suite

This repo is part of the **Agentic Evidence Suite**:
- [agentic-receipts](https://github.com/cmangun/agentic-receipts) (standard)
- [agentic-trace-cli](https://github.com/cmangun/agentic-trace-cli) (tooling)
- [agentic-artifacts](https://github.com/cmangun/agentic-artifacts) (outputs)
- [agentic-policy-engine](https://github.com/cmangun/agentic-policy-engine) (governance)
- [agentic-eval-harness](https://github.com/cmangun/agentic-eval-harness) (scenarios)
- [agentic-evidence-viewer](https://github.com/cmangun/agentic-evidence-viewer) (review UI)

## License

MIT
