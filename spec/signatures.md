# Signature Specification

## Algorithm

Ed25519 is the recommended algorithm for v1.

## Signature Envelope

```json
{
  "algorithm": "ed25519",
  "public_key": "<base64-encoded public key>",
  "value": "<base64-encoded signature>"
}
```

The signature is computed over the receipt's `hash` field.
