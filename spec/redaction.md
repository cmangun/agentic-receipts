# Redaction Semantics

A redaction replaces a field value with:

```json
{
  "redacted": true,
  "original_hash": "sha256:<hash of original value>",
  "reason": "PHI"
}
```

Hash chain remains valid because the original hash was computed before redaction.
