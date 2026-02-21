# Threat Model

| Threat | Mitigation |
|--------|-----------|
| Tampering | Hash chain detects modification |
| Reordering | Sequence numbers + prev_hash enforce order |
| Omission | Continuous chain; gaps are detectable |
| Forging | Signatures bind receipts to a known key |
| Replay | Timestamps + unique IDs prevent replay |
| Repudiation | Signed receipts provide non-repudiation |
