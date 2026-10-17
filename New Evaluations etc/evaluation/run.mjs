#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRandom } from "./src/random.mjs";
import {
  reproducibilityHash,
  runEpochSuite,
  runFusionSuite,
  runMeshSuite,
  runRangingSuite,
  runTransitSuite,
} from "./src/suites.mjs";

const root = path.dirname(fileURLToPath(import.meta.url));
const args = new Set(process.argv.slice(2));
const includeSamples = args.has("--include-samples");
const compact = args.has("--compact");
const outArg = process.argv.find((arg) => arg.startsWith("--out="));
const outputDir = path.resolve(root, outArg ? outArg.slice("--out=".length) : "outputs/latest");
const config = JSON.parse(fs.readFileSync(path.join(root, "config/experiment.config.json"), "utf8"));
const targets = JSON.parse(fs.readFileSync(path.join(root, "data/reference-targets.json"), "utf8"));

const expectedTotal = Object.values(config.suites).reduce((sum, value) => sum + value, 0);
if (expectedTotal !== config.totalScenes) throw new Error(`Suite scene counts sum to ${expectedTotal}, expected ${config.totalScenes}.`);

fs.mkdirSync(outputDir, { recursive: true });
const random = createRandom(config.seed);
const suites = {
  fusion: runFusionSuite(config, random, includeSamples),
  ranging: runRangingSuite(config, random),
  epoch: runEpochSuite(config, random, includeSamples),
  transit: runTransitSuite(config, random),
  mesh: runMeshSuite(config, random),
};
const allScenes = Object.values(suites).flatMap((suite) => suite.scenes);

const summary = {
  schemaVersion: config.schemaVersion,
  experimentId: config.experimentId,
  generatedAt: "2026-09-09T00:00:00.000Z",
  seed: config.seed,
  totalScenes: allScenes.length,
  includeSamples,
  reproducibilityHash: reproducibilityHash(allScenes),
  suites: Object.fromEntries(Object.entries(suites).map(([name, suite]) => [name, suite.summary])),
  referenceTargets: targets.targets,
  interpretation: {
    modelBased: true,
    fieldCaptureIncluded: false,
    note: "Results reproduce the published model configuration. Differences from reference targets are informative and must not be hidden by hard-coding outputs."
  }
};

const spacing = compact ? 0 : 2;
fs.writeFileSync(path.join(outputDir, "summary.json"), `${JSON.stringify(summary, null, spacing)}\n`);
fs.writeFileSync(
  path.join(outputDir, "suite-details.json"),
  `${JSON.stringify(Object.fromEntries(Object.entries(suites).map(([name, suite]) => [name, suite.summary])), null, spacing)}\n`,
);
const stream = fs.createWriteStream(path.join(outputDir, "scene-results.jsonl"));
for (const scene of allScenes) stream.write(`${JSON.stringify(scene)}\n`);
stream.end();

const completed = new Promise((resolve, reject) => {
  stream.on("finish", resolve);
  stream.on("error", reject);
});
await completed;

console.log(`MeshCrowd evaluation complete`);
console.log(`  scenes: ${allScenes.length}`);
console.log(`  seed: ${config.seed}`);
console.log(`  hash: ${summary.reproducibilityHash}`);
console.log(`  output: ${outputDir}`);
console.log(`  raw sample arrays: ${includeSamples ? "included" : "omitted (use --include-samples)"}`);