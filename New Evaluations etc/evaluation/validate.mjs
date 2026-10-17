#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(fs.readFileSync(path.join(root, "config/experiment.config.json"), "utf8"));
const sample = JSON.parse(fs.readFileSync(path.join(root, "data/samples/sample-session.json"), "utf8"));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(config.schemaVersion === "1.0.0", "Unsupported experiment config schema.");
assert(Object.values(config.suites).reduce((sum, count) => sum + count, 0) === 4161, "Suite counts must sum to 4,161.");
assert(config.ranging.rangeGateDbm > config.ranging.noiseFloorDbm, "Range gate must be stronger than the noise floor.");
assert(sample.schemaVersion === "1.0.0", "Sample session schema version mismatch.");
assert(sample.privacy.rawIdentifiersStored === false, "Raw identifiers must not be stored.");
assert(Array.isArray(sample.samples) && Array.isArray(sample.events), "Sample session arrays are missing.");
for (const entry of sample.samples) {
  assert(entry.linkIdHash.startsWith("sha256:"), "Link identifiers must be pseudonymised.");
  assert(entry.rssiDbm >= -127 && entry.rssiDbm <= 20, "RSSI lies outside the Android scan range.");
}

const summaryPath = path.join(root, "outputs/latest/summary.json");
if (fs.existsSync(summaryPath)) {
  const summary = JSON.parse(fs.readFileSync(summaryPath, "utf8"));
  assert(summary.totalScenes === config.totalScenes, "Generated scene count mismatch.");
  assert(summary.reproducibilityHash.startsWith("sha256:"), "Missing reproducibility hash.");
}

console.log("MeshCrowd evaluation package validation passed.");