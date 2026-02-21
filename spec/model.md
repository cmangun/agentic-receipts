# Receipt Model

## Overview

A receipt is a cryptographic attestation that a specific event occurred in an agent trace.

## Receipt Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| receipt_id | UUID | Yes | Unique identifier |
| event_id | UUID | Yes | Reference to the trace event |
| hash | string | Yes | SHA-256 hash of canonical event |
| prev_hash | string | Yes | Hash of previous receipt (or "genesis") |
| timestamp | ISO 8601 | Yes | When the receipt was created |
| event_type | enum | Yes | Category of the event |
| signature | object | No | Cryptographic signature envelope |
