# MeshCrowd evaluation data dictionary

## Session document

An APK evaluation export is one JSON object conforming to `schemas/session.schema.json`.

| Field | Type | Description |
|---|---|---|
| `schemaVersion` | string | Export contract version. This package uses `1.0.0`. |
| `sessionId` | string | Unique evaluation run identifier. |
| `createdAt`, `completedAt` | ISO-8601 string | UTC session timestamps. |
| `device.pseudonymousId` | string | Per-session salted SHA-256 pseudonym; not a hardware identifier. |
| `privacy` | object | Explicit record that camera/microphone/raw identifiers are not retained and whether geo is included. |
| `configuration` | object | Radius, dBm gate/floor, epoch duration, and stable-sample count used by the APK. |
| `samples` | array | Per-link RSSI observations. |
| `events` | array | Closed attenuation events and their multivariate features. |
| `epochs` | array | Stored scan windows and field-change verdicts. |
| `transit` | array | RFCOMM/L2CAP barrier observations. |
| `mesh` | array | Multi-node confirmation and reliability records. |
| `rewards` | array | XP, fusion bonus, and reliability multiplier ledger. |
| `summary` | object | End-of-session counters. |

## RSSI sample

| Field | Unit | Description |
|---|---|---|
| `timestampMs` | Unix ms | Observation time. |
| `epochId` | — | Epoch containing the sample. |
| `linkIdHash` | — | `sha256:` pseudonym generated with a per-session salt. |
| `radioBand` | enum | `ble`, `wifi24`, `wifi5`, `rfcomm`, or `l2cap`. |
| `frequencyMhz` | MHz | Channel centre frequency, when the Android API supplies it. |
| `rssiDbm` | dBm | Received signal strength in the Android range −127…20. |

## Event features

| Field | Unit | Description |
|---|---|---|
| `depthDb` | dB | Maximum dip below the adaptive baseline. |
| `durationMs` | ms | Sustained event duration. |
| `texture` | ratio | In-event jitter relative to dip depth. |
| `varianceDb2` | dB² | Variance of the event series. |
| `prominenceDb` | dB | Peak depth relative to competing peaks. |
| `coherentLinks` | count | Links registering the event in a common interval. |
| `classification` | enum | `pedestrian`, `vehicle`, `disturbance`, or `unknown`. |
| `confidence` | 0…1 | Classifier confidence. |
| `range.status` | enum | `estimated-band`, `refused`, or `noise-floor`. |

## Experiment outputs

`run.mjs` emits:

- `summary.json`: top-level metrics, reference targets, and reproducibility SHA-256.
- `suite-details.json`: aggregate metrics for fusion, ranging, epochs, transit, and mesh.
- `scene-results.jsonl`: one JSON object per scene (4,161 lines). JSON Lines is used for streaming and can be processed without loading the full corpus into memory.

Run with `--include-samples` to include generated RSSI arrays in fusion and epoch scene records.