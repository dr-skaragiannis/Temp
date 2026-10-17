#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRandom } from "../src/random.mjs";
import { estimateRange, robustMeshConsensus, rssiAtDistance } from "../src/model.mjs";
import { runEpochSuite, runFusionSuite, runMeshSuite, runRangingSuite, runTransitSuite } from "../src/suites.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const config = JSON.parse(fs.readFileSync(path.join(root, "config/experiment.config.json"), "utf8"));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const randomA = createRandom(config.seed);
const randomB = createRandom(config.seed);
for (let index = 0; index < 100; index += 1) {
  assert(randomA.next() === randomB.next(), "Seeded PRNG is not deterministic.");
}

const ble = config.bands.ble;
assert(Math.abs(rssiAtDistance(1, ble) - ble.referenceRssiDbmAt1m) < 1e-9, "1 m RSSI reference mismatch.");
assert(estimateRange(-60, ble, config.ranging).status === "estimated-band", "Strong link must return a band.");
assert(estimateRange(-80, ble, config.ranging).status === "refused", "Weak link must be refused.");
assert(estimateRange(-92, ble, config.ranging).status === "noise-floor", "Noise-floor link must be excluded.");

const consensus = robustMeshConsensus(
  [
    { nodeId: "node-1", count: 2, byzantine: false },
    { nodeId: "node-2", count: 2, byzantine: false },
    { nodeId: "node-3", count: 8, byzantine: true },
  ],
  config,
);
assert(consensus.fusedCount === 2 && consensus.confirmed, "Robust mesh failed to preserve the honest majority.");
assert(consensus.reports.find((report) => report.nodeId === "node-3").accepted === false, "Byzantine outlier was accepted.");

const random = createRandom(config.seed);
const suites = [
  runFusionSuite(config, random, false),
  runRangingSuite(config, random),
  runEpochSuite(config, random, false),
  runTransitSuite(config, random),
  runMeshSuite(config, random),
];
const total = suites.reduce((sum, suite) => sum + suite.scenes.length, 0);
assert(total === 4161, `Expected 4,161 scenes, received ${total}.`);
assert(suites.every((suite) => suite.scenes.length > 0), "A suite returned no scenes.");

console.log("MeshCrowd evaluation self-tests passed.");