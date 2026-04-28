# Non-goals

What `agentic-receipts` deliberately does not try to be. Each item names a delegation point or an explicit boundary; conflating these with what receipts is responsible for is one of the most common sources of design confusion in this problem space.

## Not a transport layer

Receipts define structure (canonicalized fields, hash chain, signature) but do not specify how records move between systems. Transport delegates to OpenTelemetry for observability streams, CloudEvents for cross-system events, and direct file or object handoff for bundles. See `INTEROP.md` in the meta-repo for the per-standard mappings.

## Not a storage layer

The chain integrity property catches violations regardless of storage substrate. Adopters use ordinary object storage, ordinary filesystems, or specialized transparency logs — receipts has no opinion. The advisory storage policy ("append-only-recommended") is defense-in-depth, not the primary enforcement mechanism.

## Not a runtime

This repo is a specification: schemas, canonicalization rules, hashing, signing, redaction, and conformance vectors. Implementations live in component repos that depend on the spec; there is no executable agent runtime here.

## Not an agent sandbox

Receipts record what an agent did. They do not isolate execution, restrict capabilities, or enforce resource limits. Sandboxing — containerization, capability restriction, runtime instrumentation — belongs to the agent runtime layer.

## Not a correctness oracle

Receipts prove what happened, not whether what happened was *right*. An agent that consistently makes wrong-but-permitted decisions produces beautifully-verifiable receipts of those wrong decisions. Correctness is owned by evaluation and human review, not by the verifiability layer.
